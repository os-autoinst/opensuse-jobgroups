# Repository for openqa.opensuse.org job groups

This git repo contains the jobgroup definitions for openqa.opensuse.org.
Changes to the repo are automatically checked by CI and applied to openqa.opensuse.org.

You can find the individual jobgroups in the `job_groups` directory.
The mapping of the serverside job group IDs to these files is done in `job_groups.yaml`.

## tool.py

All operations in this repo can be done using the `tool.py` script.
It only uses python3 standard libraries but it requires `openqa-cli`
tool to be installed.

For most operations it needs API credentials for openqa.opensuse.org.
They can be supplied in three different ways:

* `APIKEY` and `APISECRET` environment variables
* `~/.config/openqa/client.conf`
* `/etc/openqa/client.conf`

It always must be called with the root of this git repo as the
current working directory.

For more information refer to `./tool.py --help`.

## yamllint and yamltidy

The CI uses yamllint to check if the yaml files are wellformed.
To tidy up your yaml, you can make use of [yamltidy](https://github.com/perlpunk/yamltidy).
Simply run `yamltidy -i job_groups/my_file.yaml`.
This repo comes with sane default configurations that will be automatically used for both
tools.


## Adding a new job group

First create the jobgroup on the server and get the group id from the url.

Then use `tool.py` to add the jobgroup to the mapping file (`job_groups.yaml`):
```
$ ./tool.py --gendb -j 86
86: sles_12_sp3_powerpc
```

Finally download the jobgroup yaml template:
```
$ ./tool.py --fetch -j 86
Fetching 86 -> sles_12_sp3_powerpc
```

## Conflicts in CI due to already existing job templates in other scenarios

Sometimes when reworking job groups one might find that there are failures in the CI,
e.g. #919 wants to move some tests from `job_groups/opensuse_tumbleweed_aarch64.yaml`
to a new job group `job_groups/opensuse_tumbleweed_legacy_arm.yaml` and the CI fails:

> Job template name 'jeos' with opensuse-Tumbleweed-JeOS-for-AArch64-armv7hl and aarch32-HD20G is already used in job group 'openSUSE Tumbleweed AArch64'

While the usual solution is to submit changes separately (one PR removes, a second
PR adds), if `tool.py` can read the openQA API keys, then it is possible to do a manual
deploy of some or all of the changes (preferably the one that removes the
test suites), and then trigger the CI again either with a new commit or by force
pushing.

```bash
./tool.py --push -j 3
```
