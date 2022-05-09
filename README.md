# Repository for openqa.opensuse.org job groups

This git repo contains the jobgroup definitions for openqa.opensuse.org.
Changes to the repo are automatically checked by CI and applied to openqa.opensuse.org.

You can find the individual jobgroups in the `job_groups` directory.
The mapping of the serverside job group IDs to these files is done in `job_groups.yaml`.


## Adding a new job group

First create the jobgroup on the server and get the group id from the url.
Then use `tool.py` to download the jobgroup yaml template:
```
$ ./tool.py --fetch -j 86
Fetching 86 -> sles_12_sp3_powerpc
```

Finally add the job group with it's id (as printed by `tool.py`) to `job_groups.yaml`:
```yaml
86: sles_12_sp3_powerpc
```
