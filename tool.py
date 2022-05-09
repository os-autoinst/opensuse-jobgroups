#!/usr/bin/python3

import os
import sys
import json
import yaml
import math
import argparse
import configparser
import subprocess
from textwrap import dedent


def get_api_credentials():
	user_config = os.path.expanduser("~/.config/openqa/client.conf")
	system_config = "/etc/openqa/client.conf"
	if os.environ.get('APIKEY') and os.environ.get('APISECRET'):
		print("Getting APIKEY and APISECRET from environment.", file=sys.stderr)
		return (os.environ['APIKEY'], os.environ['APISECRET'])
	if os.path.exists(user_config):
		config = configparser.ConfigParser()
		config.read(user_config)
		if "openqa.opensuse.org" in config.sections():
			print("Getting APIKEY and APISECRET from '%s'" % user_config, file=sys.stderr)
			return (
				config.get("openqa.opensuse.org", "KEY"),
				config.get("openqa.opensuse.org", "SECRET")
			)
	if os.path.exists(system_config) and os.access(system_config, os.R_OK):
		config = configparser.ConfigParser()
		config.read(system_config)
		if "openqa.opensuse.org" in config.sections():
			print("Getting APIKEY and APISECRET from '%s'" % system_config, file=sys.stderr)
			return (
				config.get("openqa.opensuse.org", "KEY"),
				config.get("openqa.opensuse.org", "SECRET")
			)
	print("Error: Unable to get API credentials", file=sys.stderr)


api_credentials = None
def api_request(*args):
	global api_credentials
	if not api_credentials:
		api_credentials = get_api_credentials()
	APIKEY, APISECRET = api_credentials
	cmd = ['openqa-cli', 'api', '--o3', '-q']
	cmd.extend(['--apikey', APIKEY, '--apisecret', APISECRET])
	cmd.extend(args)
	try:
		output = subprocess.check_output(cmd)
	except subprocess.CalledProcessError as e:
		print("Error: API call %r returned exit code '%i'" % (args, e.returncode), file=sys.stderr)
		output = e.output
	try:
		j = json.loads(output)
	except json.decoder.JSONDecodeError:
		print("Error: openqa-cli returned: %s" % output)
		os._exit(1)
	return j


def show_server_error(r):
	try:
		assert not isinstance(e, str)
		for e in r['error']:
			if isinstance(e, dict):
				e = "  YAML Path: %(path)s\n  Message: %(message)s" % e
			print("Error %i:\n%s" % (r['error_status'], e), file=sys.stderr)
	except:
		print("Error %(error_status)i: %(error)s" % r, file=sys.stderr)


def generate_header(filename):
	content = [
		"WARNING",
		"",
		"This file is managed in GIT!",
		"Any changes via the openQA WebUI will get overwritten!",
		"",
		"https://github.com/os-autoinst/opensuse-jobgroups",
		filename
	]
	line_length = max(max([len(line)+4 for line in content]), 58)
	content.insert(0, '#' * line_length)
	content.append('#' * line_length)
	def _align(line):
		prefix_len = math.floor((line_length - len(line)) / 2)
		suffix_len = math.ceil((line_length - len(line)) / 2)
		return ' ' * prefix_len + line + ' ' * suffix_len
	return "\n".join(map(lambda l: "#%s#" % l, map(_align, content)))

parser = argparse.ArgumentParser(
	description = 'Fetch and push jobgroups from and to openqa.opensuse.org',
	epilog = dedent("""
		You may provide tha API credentials via env vars (APIKEY/APISECRET),
		via ~/.config/openqa/client.conf or via /etc/openqa/client.conf.
	""")
)

parser.add_argument('--dry-run', action='store_true', help="Don't actually do anything. In push mode do serverside check via preview=1")
parser.add_argument('--gendb', action='store_true', help="Generate job_groups.yaml from O3")
parser.add_argument('--orphans', action='store_true', help="Check that there are job_group files that are not defined in job_groups.yaml")
parser.add_argument('--fetch', action='store_true', help="Download all jobgroups as defined in job_groups.yaml")
parser.add_argument('--push', action='store_true', help="Upload all jobgroups as defined in job_groups.yaml")
parser.add_argument('-j', dest='filter_job_group', type=int, help="Perform fetch or push action only for this jobgroup id")
parser.add_argument('-f', dest='filter_file_name', type=str, help="Perform fetch or push action only for this jobgroup yaml file")
args = parser.parse_args()

if not (args.fetch or args.push or args.gendb or args.orphans):
	parser.print_help()
	os._exit(1)


# (try to) load job_groups.yaml
try:
	job_groups_db = yaml.safe_load(open('job_groups.yaml'))
except FileNotFoundError:
	job_groups_db = {}

# get everything we need from the api using only a single request
job_groups = sorted(api_request('job_groups'), key=lambda i: i['id'])



if args.gendb:
	job_groups_db = {}
	for job_group in job_groups:
		fs_name = job_group['name'].strip().lower().\
			replace(' ', '_').\
			replace('(', '').replace(')', '').\
			replace(':', '').replace('/', '').\
			replace('_-_', '-').\
			replace(',', '').replace('+', '').\
			replace('__', '_').\
			replace('[deprecated]', 'DEPRECATED')
		job_groups_db[job_group['id']] = fs_name
		print(yaml.safe_dump({job_group['id']: fs_name}).strip())
		#print("%(id)i: %(name)s" % job_group)
	if not args.dry_run:
		yaml.safe_dump(job_groups_db, open('job_groups.yaml', 'w'))

elif args.fetch:
	job_groups_by_id = {}
	for job_group in job_groups:
		job_groups_by_id[job_group['id']] = job_group

	for gid, gname in job_groups_db.items():
		if args.filter_job_group and args.filter_job_group != gid:
			continue
		if args.filter_file_name and os.path.basename(args.filter_file_name) not in (gname, '%s.yaml' % gname):
			continue
		print("Fetching %i -> %s" % (gid, gname), file=sys.stderr)
		job_group = job_groups_by_id[gid]
		if not args.dry_run:
			template = job_group['template']
			filename = 'job_groups/%s.yaml' % gname
			if not "This file is managed in GIT" in template:
				template = generate_header(filename) + "\n" + template
			open(filename, 'w').write(template)

elif args.push:
	job_groups_by_id = {}
	for job_group in job_groups:
		job_groups_by_id[job_group['id']] = job_group

	exit_code = 0
	for gid, gname in job_groups_db.items():
		if args.filter_job_group and args.filter_job_group != gid:
			continue
		if args.filter_file_name and os.path.basename(args.filter_file_name) not in (gname, '%s.yaml' % gname):
			continue
		job_group = job_groups_by_id[gid]
		if args.dry_run:
			print("Checking %s -> %i" % (gname, gid), file=sys.stderr)
			r = api_request('-X', 'POST', 'job_templates_scheduling/%i' % gid, 'schema=JobTemplates-01.yaml',
				'preview=1', '--param-file', 'template=job_groups/%s.yaml' % gname
			)
			if r.get('error'):
				show_server_error(r)
				exit_code = 1 # let's show the user all the error at once
			elif r.get('changes'):
				print('  ' + r['changes'].replace("\n", "\n  "), file=sys.stderr)
		else:
			print("Pushing %s -> %i" % (gname, gid), file=sys.stderr)
			r = api_request('-X', 'POST', 'job_templates_scheduling/%i' % gid, 'schema=JobTemplates-01.yaml',
				'preview=0', '--param-file', 'template=job_groups/%s.yaml' % gname
			)
			if r.get('error'):
				show_server_error(r)
				os._exit(1) # let's stop on the first error here
			elif r.get('changes'):
				print('  ' + r['changes'].replace("\n", "\n  "), file=sys.stderr)
	os._exit(exit_code)

elif args.orphans:
	job_groups_yaml = {'%s.yaml' % v: k for k, v in job_groups_db.items()}
	exit_code = 0
	for job_group_file in os.listdir('job_groups'):
		if job_group_file not in job_groups_yaml:
			print("Found orphaned file: %s" % job_group_file, file=sys.stderr)
			exit_code = 1
	os._exit(exit_code)
