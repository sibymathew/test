#!/bin/bash

git_short_commit_id=`echo $CIRCLE_SHA1 | cut -b 1-8`

echo $git_short_commit_id
`export GIT_COMMIT="$git_short_commit_id"`
