#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  release_wave.sh start --wave <wave-number> [--base <base-branch>] [--push]
  release_wave.sh complete --wave <wave-number> --ticket <ticket-id> --outcome <outcome> [--target <target-branch>] [--push]

Commands:
  start     Create or update the release/v2025.<wave-number> branch from the base branch.
  complete  Squash merge the release branch into the target branch and record the ticket reference.

Options:
  --wave       Required wave identifier (e.g. 1, 2a).
  --ticket     Work item or ticket identifier used in the squash commit message.
  --outcome    Wave outcome description used for tagging (e.g. success, rollback).
  --base       Branch to branch from when creating the release branch (default: main).
  --target     Branch to merge into when completing the wave (default: main).
  --push       Push changes (branch, commit) to the remote "origin" once local operations succeed.
  --help       Show this message and exit.
USAGE
}

require_clean_tree() {
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "ERROR: Working tree must be clean before running this command." >&2
    exit 1
  fi
}

ensure_branch_exists() {
  local branch="$1"
  if git show-ref --verify --quiet "refs/heads/${branch}"; then
    return 0
  fi
  if git ls-remote --exit-code --heads origin "${branch}" >/dev/null 2>&1; then
    git fetch origin "${branch}:${branch}"
  fi
}

create_release_branch() {
  local wave="$1"
  local base="$2"
  local push_flag="$3"
  local branch="release/v2025.${wave}"

  require_clean_tree

  git fetch origin "${base}:${base}" >/dev/null 2>&1 || git fetch origin "${base}" || true
  git checkout "${base}"
  git pull --ff-only origin "${base}"

  if git show-ref --verify --quiet "refs/heads/${branch}"; then
    git checkout "${branch}"
    git merge --ff-only "${base}"
  else
    git checkout -b "${branch}" "${base}"
  fi

  if [[ "${push_flag}" == "true" ]]; then
    git push -u origin "${branch}"
  fi

  echo "Created/updated ${branch} from ${base}."
}

complete_release_wave() {
  local wave="$1"
  local ticket="$2"
  local outcome="$3"
  local target="$4"
  local push_flag="$5"
  local branch="release/v2025.${wave}"

  require_clean_tree

  ensure_branch_exists "${branch}"

  git checkout "${target}"
  git pull --ff-only origin "${target}" || true
  git checkout "${target}"
  git merge --squash "${branch}"

  local commit_message="Wave ${wave} (${outcome}) [${ticket}]"
  git commit -m "${commit_message}"

  if [[ "${push_flag}" == "true" ]]; then
    git push origin "${target}"
  fi

  echo "Squash merged ${branch} into ${target} with message: ${commit_message}"
  echo "Remember to run the Azure DevOps release pipeline to tag the wave automatically."
}

main() {
  if [[ $# -eq 0 ]]; then
    usage
    exit 1
  fi

  local command="$1"

  if [[ "${command}" == "--help" || "${command}" == "-h" ]]; then
    usage
    exit 0
  fi

  shift

  local wave=""
  local ticket=""
  local outcome=""
  local base="main"
  local target="main"
  local push_flag="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --wave)
        wave="$2"
        shift 2
        ;;
      --ticket)
        ticket="$2"
        shift 2
        ;;
      --outcome)
        outcome="$2"
        shift 2
        ;;
      --base)
        base="$2"
        shift 2
        ;;
      --target)
        target="$2"
        shift 2
        ;;
      --push)
        push_flag="true"
        shift 1
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option: $1" >&2
        usage
        exit 1
        ;;
    esac
  done

  if [[ -z "${wave}" ]]; then
    echo "ERROR: --wave is required." >&2
    exit 1
  fi

  if [[ "${wave}" == *"/"* ]]; then
    echo "ERROR: Wave identifier must not contain '/' characters." >&2
    exit 1
  fi

  case "${command}" in
    start)
      create_release_branch "${wave}" "${base}" "${push_flag}"
      ;;
    complete)
      if [[ -z "${ticket}" ]]; then
        echo "ERROR: --ticket is required for the complete command." >&2
        exit 1
      fi
      if [[ -z "${outcome}" ]]; then
        echo "ERROR: --outcome is required for the complete command." >&2
        exit 1
      fi
      complete_release_wave "${wave}" "${ticket}" "${outcome}" "${target}" "${push_flag}"
      ;;
    *)
      echo "Unknown command: ${command}" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
