#!/bin/bash

set -Ceu

SCRIPT_FILE_NAME=$(basename $0)
SCRIPT_NAME=${SCRIPT_FILE_NAME%.*}
SELF=$(cd $(dirname $0); pwd)
LOGGING=false
VERSION="0.1.0"
SEPARATER='---------------------------'

function _usage() {
    echo "Usage: ${SCRIPT_NAME} [OPTIONS] FILE"
    echo "  This is the boilerplate for shell script."
    echo
    echo "Options:"
    echo "  -h, --help                     Show help"
    echo "  -v, --version                  Show script version"
    echo "  -a, --long-a ARG               Option which must have argument"
    echo "  -b, --long-b [ARG]             Either with or without argument is possible"
    echo "  -c, --long-c                   Option without argument"
    echo "      --verbose                  Print various logging information"
    echo
    exit 0
}

function _log() {
    ${LOGGING} && echo "$@" || return 0
}

function _err() {
    echo "$1" && exit 1
}

function _is_cmd_exist() {
    type $@ > /dev/null 2>&1
}

function _is_file_exist() {
    [ -f $1 ] > /dev/null 2>&1
}

function _is_dir_exist() {
    [ -d $1 ] > /dev/null 2>&1
}

# -------------------------------------------------------------

ARG_VALUES=()
OPT_A=""
OPT_B=""
OPT_C=false
IS_FLAG_P=false
IS_FLAG_Z=false

function _main() {
    DIST_DIR='dist'
    rm -rf ${DIST_DIR}
    mkdir -p ${DIST_DIR}/{a4l,a3}

    # --------------------------------------------------------------

#        print_ope=''
#        if [ "${operator}" == "add" ]; then
#            print_ope='tasu'
#        elif [ "${operator}" == "sub" ]; then
#            print_ope='hiku'
#        elif [ "${operator}" == "mul" ]; then
#            print_ope='kakeru'
#        elif [ "${operator}" == "div" ]; then
#            print_ope='waru'
#        elif [ "${operator}" == "mix" ]; then
#            print_ope='mix'
#        fi

    params=(
        "ope -a 1 -b 1 -o add -c 3 -r 10"
        "ope -a 2 -b 1 -o add -c 3 -r 10"
        "aBc -a 2 -b 1 -o add -c 3 -r 10"
        "ope -a 2 -b 1 -o mul -c 3 -r 10"
        "ope --a-min 10 --a-max 19 --b-min 10 --b-max 19 -o mul -c 3 -r 10"
        "ope -a 2 --b-min 11 --b-max 11 -o mul -c 3 -r 10"
    )
    for size in a3 a4l; do
        [ "${size}" == "a3" ] && page=5 || page=10
        100masu.py ${size} ope -a 1 -b 1 -o add -c 3 -r 15 -p ${page} -w \
            --out-file "${DIST_DIR}/${size}/step-01.pdf"
        100masu.py ${size} ope -a 2 -b 1 -o add -c 3 -r 15 -p ${page} -w \
            --out-file "${DIST_DIR}/${size}/step-02.pdf"
        100masu.py ${size} aBc -a 2 -b 1 -o add -c 3 -r 15 -p ${page} -w \
            --out-file "${DIST_DIR}/${size}/step-03.pdf"
        100masu.py ${size} ope -a 2 -b 1 -o mul -c 3 -r 15 -p ${page} -w \
            --out-file "${DIST_DIR}/${size}/step-04.pdf"
        100masu.py ${size} ope --a-min 10 --a-max 19 --b-min 10 --b-max 19 -o mul -c 3 -r 15 -p ${page} -w \
            --out-file "${DIST_DIR}/${size}/step-05.pdf"
        100masu.py ${size} ope -a 2 --b-min 11 --b-max 11 -o mul -c 3 -r 15 -p ${page} -w \
            --out-file "${DIST_DIR}/${size}/step-06.pdf"
        echo "done ${size}"
    done
}

# -------------------------------------------------------------

function _init() {
    while (( $# > 0 )); do
        case $1 in
            -h | --help)
                _usage
                exit 1
                ;;
            -v | --version)
                echo ${SCRIPT_NAME} v${VERSION}
                exit 0
                ;;
            --verbose)
                LOGGING=true
                shift
                ;;

            # Must have argument
            -a | --long-a)
                set +u
                if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                    _err "-a option requires a value."
                fi
                set -u
                OPT_A=$2
                shift 2
                ;;

            # Either with or without argument is possible
            -b | --long-b)
                set +u
                if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                    shift
                else
                    OPT_B=$2
                    shift 2
                fi
                set -u
                ;;

            # no argument
            -c | --long-c)
                shift 1
                ;;

            # after this all args include '-xx', will treat arg value
            -- | -)
                shift 1
                ARG_VALUES+=( "$@" )
                break
                ;;

            # for true or false flags, no argument
            --*)
                if [[ "$1" =~ 'z' ]]; then
                    IS_FLAG_Z='true'
                fi
                shift
                ;;

            # for true or false flags, no argument
            -*)
                if [[ "$1" =~ 'b' ]]; then
                    IS_FLAG_P='true'
                fi
                shift
                ;;

            # arguments
            *)
                ARG_VALUES+=("$1")
                shift
                ;;
        esac
    done

    _set_static_var
}

function _set_static_var() {
    ARG_VALUES=$@
}

function _verbose() {
    _log "ARG_VALUES: ${ARG_VALUES[@]}"
    _log "OPT_A: ${OPT_A}"
    _log "OPT_B: ${OPT_B}"
    _log "IS_FLAG_P: ${IS_FLAG_P}"
    _log "${SEPARATER}"
}

function _verify_static_var() {
    :
}

function _args_check() {
    :
    #if [ ${#ARG_VALUES[@]} -eq 0 ]; then
    #    _err 'no argument.'
    #elif ! _is_file_exist ${ARG_VALUES[0]}; then
    #    _err 'No such file.'
    #fi
}

# -------------------------------------------------------------
# Main Routine
# -------------------------------------------------------------
_init $@ && _args_check && _verbose && {
    _log 'start main process..' && _log "${SEPARATER}"
    _main
}
exit 0

