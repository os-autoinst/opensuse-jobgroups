# Just a helper for me

.PHONY: devel
devel:
	python3 tool.py --gendb -j 38
	python3 tool.py --fetch -j 38

.PHONY: devel-push
devel-push:
	python3 tool.py --push -j 38
