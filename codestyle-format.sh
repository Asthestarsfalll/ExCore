#!/usr/bin/env bash


format() {
    local path=$1 
    local check=$2
    local check_only=$3

    py_files=$(find $path -name '*.py')
    target="__init__.py"
    echo "use 'black' to format code"
    black $py_files -q
    echo "use 'isort' to sort imports"
    isort $py_files -q
    echo "use 'autoflake' to remove-unused-variables"
    autoflake -r --in-place --remove-unused-variables $py_files
    if [ $check = true ]; then
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
    fi
}


# check_only=${1:-false}
# echo $check_only
echo "format 'tests'"
format "tests/" false
echo "format 'excore'"
format "excore/" true 
