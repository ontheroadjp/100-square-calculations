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

    mkdir -p ${DIST_DIR}/mental_arithmetic/{20,45}/{A3,A4}

    for i in {1..9}; do
        mkdir -p ${DIST_DIR}/99/{20,45}/{A3,A4}/0${i}
        mkdir -p ${DIST_DIR}/99/{20,45}/{A3,A4}/{descend,random}/0${i}
        mkdir -p ${DIST_DIR}/99/{20,45}/{A3,A4}/mix
    done

#    exit 0


    _basic
#    _kuku
#    _kuku_descend
#    _kuku_random
#    _kuku_all_mix
#
}

function _basic {
    c=2
    r=10
    for long in 20 45; do
        [ ${long} == 45 ] && {
            c=3
            r=15
        }
        for size in a3 a4; do
            # Basic training
            [ "${size}" == "a3" ] && page=5 || page=10
            100masu.py ${size} ope -a 1 -b 1 -o add -c ${c} -r ${r} -p ${page} \
                --out-file "${DIST_DIR}/mental_arithmetic/${long}/${size}/step-01.pdf"
            100masu.py ${size} ope -a 2 -b 1 -o add -c ${c} -r ${r} -p ${page} \
                --out-file "${DIST_DIR}/mental_arithmetic/${long}/${size}/step-02.pdf"
            100masu.py ${size} ope -a 1 -b 1 -o mul -c ${c} -r ${r} -p ${page} --shuffle \
                --out-file "${DIST_DIR}/mental_arithmetic/${long}/${size}/step-03.pdf"

            # Mental althmatic training
            100masu.py ${size} aBc -a 2 -b 1 -o add -c ${c} -r ${r} -p ${page} \
                --out-file "${DIST_DIR}/mental_arithmetic/${long}/${size}/step-04.pdf"

            # Practical training
            100masu.py ${size} ope -a 2 -b 1 -o mul -c ${c} -r ${r} -p ${page} \
                --out-file "${DIST_DIR}/mental_arithmetic/${long}/${size}/step-05.pdf"
            100masu.py ${size} ope --a-min 10 --a-max 19 --b-min 10 --b-max 19 \
                -o mul -c ${c} -r ${r} --shuffle -p ${page} \
                --out-file "${DIST_DIR}/mental_arithmetic/${long}/${size}/step-06.pdf"
            100masu.py ${size} squ -a 5 -o mul -c ${c} -r ${r} --shuffle -p ${page} \
                --out-file "${DIST_DIR}/mental_arithmetic/${long}/${size}/step-07.pdf"
            100masu.py ${size} ope -a 2 --b-min 11 --b-max 11 \
                -o mul -c ${c} -r ${r} -p ${page} \
                --out-file "${DIST_DIR}/mental_arithmetic/${long}/${size}/step-08.pdf"
            echo "done ${size}"
        done
    done
}

function _kuku() {
    for size in a3 a4; do
        [ "${size}" == "a3" ] && page=1 || page=1
        [ "${size}" == "a3" ] && out=A3 || out=A4
        for dan in 1 2 3 4 5 6 7 8 9; do
            100masu.py ${size} 99 -a ${dan} -c 3 -r 9 -p ${page} \
                --out-file "${DIST_DIR}/99/0${dan}/0${dan}-${size}.pdf"
        done
        echo "done ${size}"
    done
}
function _kuku_descend() {
    for size in a3 a4l; do
        [ "${size}" == "a3" ] && page=1 || page=1
        for dan in 1 2 3 4 5 6 7 8 9; do
            100masu.py ${size} 99 -a ${dan} -c 3 -r 9 -p ${page} --reverse \
                --out-file "${DIST_DIR}/99/0${dan}_descend/0${dan}-${size}-descend.pdf"
        done
        echo "done ${size}"
    done
}
function _kuku_random() {
    for size in a3 a4l; do
        [ "${size}" == "a3" ] && page=1 || page=1
        for dan in 1 2 3 4 5 6 7 8 9; do
            100masu.py ${size} 99 -a ${dan} -c 3 -r 9 -p ${page} --shuffle \
                --out-file "${DIST_DIR}/99/0${dan}_random/0${dan}-${size}-random.pdf"
        done
        echo "done ${size}"
    done
}
function _kuku_all_mix() {
    for size in a3 a4l; do
        [ "${size}" == "a3" ] && page=5 || page=10
        100masu.py ${size} ope --a-min 1 --a-max 9 --b-min 1 --b-max 9 \
            -o mul -c 3 -r 15 -p ${page} --shuffle \
            --out-file "${DIST_DIR}/99/mix/mix-${size}.pdf"
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

