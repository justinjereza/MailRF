.PHONY: test clean

test:
	@trial tests;
	@cat _trial_temp/test.log;

clean:
	@rm -rf _trial_temp;
	@find ${PWD} -type f -name '*.py[co]' -exec rm {} +;
	@find ${PWD} -type f -name '.DS_Store' -exec rm {} +;
