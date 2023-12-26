#!/usr/bin/env bash

check=$1

if [ "$check" = "all" ]; then
    git_files=$(git ls-files)
    py_files=$(echo "$git_files" | grep '.py$')
else
    py_files=$(git diff --name-only --cached | grep '.py$')
fi

if [ "$py_files" ]; then
    target="__init__.py"
    echo "use 'black' to format code"
    black $py_files -q
    echo "use 'isort' to sort imports"
    isort $py_files -q
    echo "use 'autoflake' to remove-unused-variables"
    autoflake -r --in-place --remove-unused-variables $py_files

    echo "use 'pylint' to check codestyle"
    pylint $py_files --rcfile=.pylintrc || pylint_ret=$?
    if [ "$pylint_ret" ]; then
        echo "'pylint' check failed"
        exit $pylint_ret
    fi
    echo "use 'flake8' to check codestyle"
    for file in $py_files 
    do
        if ! [[ $file =~ $target ]]; then
            flake8 --max-line-length 100 --max-doc-length 120 $file || flake8_ret=$?
        fi
    if [ "$flake8_ret" ]; then
        echo "'flake8' check failed"
        exit $flake8_ret
    fi
    done
else
    echo "No files to format"
fi
