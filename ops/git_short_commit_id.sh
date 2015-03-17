#!/bin/bash

git_short_commit_id=`echo $CIRCLE_SHA1 | cut -b 1-8`
echo export GIT_COMMIT=$git_short_commit_id > ops/sourcefile
