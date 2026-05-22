#!/usr/bin/env bash
# Integration tests for claude-auto-retry. Requires tmux.
# Run from the plugin root: bash tests/integration/run.sh
set -euo pipefail

if ! command -v tmux >/dev/null 2>&1; then
  echo "SKIP: tmux not installed"
  exit 0
fi

PLUGIN_DIR=$(cd "$(dirname "$0")/../.." && pwd)
ENGINE="$PLUGIN_DIR/hooks/auto_retry.py"
WORK=$(mktemp -d)
TMUX_BIN=$(command -v tmux)

# PATH shim: every `tmux` call (from the engine too) routes through our
# isolated -L it-test server, so send-keys targets the right pane.
cat > "$WORK/tmux" <<SHIM
#!/usr/bin/env bash
exec "$TMUX_BIN" -L it-test "\$@"
SHIM
chmod +x "$WORK/tmux"
export PATH="$WORK:$PATH"

trap "\"$TMUX_BIN\" -L it-test kill-server 2>/dev/null || true; rm -rf '$WORK'" EXIT

export CLAUDE_AUTO_RETRY_LOG_PATH="$WORK/log.jsonl"
export CLAUDE_AUTO_RETRY_PENDING_DIR="$WORK/pending"
export CLAUDE_AUTO_RETRY_SENTINEL_DIR="$WORK/sentinel"
export CLAUDE_AUTO_RETRY_USER_CONFIG="$WORK/nope.toml"
mkdir -p "$CLAUDE_AUTO_RETRY_SENTINEL_DIR"

# Now `tmux` (via shim) uses -L it-test for the engine too.
tmux new-session -d -s test 'cat'
TMUX_PANE=$(tmux list-panes -t test -F '#{pane_id}')
echo "Test pane: $TMUX_PANE"

# Project config: 1s transient backoff, quiet (no display-message).
mkdir -p "$WORK/.claude"
cat > "$WORK/.claude/claude-auto-retry.toml" <<TOML
[backoff]
rate_limit_transient = 1
quiet = true
TOML

EVT='{"hook_event_name":"StopFailure","error":"rate_limit","error_details":"Server is temporarily limiting","session_id":"itest","cwd":"'$WORK'"}'

echo "Test 1: end-to-end injection"
TMUX_PANE="$TMUX_PANE" bash -c "echo '$EVT' | python3 '$ENGINE' --hook"

# Wait up to 8s for the retry to fire
for _ in 1 2 3 4 5 6 7 8; do
  sleep 1
  if grep -q '"outcome": "fired"' "$CLAUDE_AUTO_RETRY_LOG_PATH" 2>/dev/null; then
    break
  fi
done

if ! grep -q '"outcome": "fired"' "$CLAUDE_AUTO_RETRY_LOG_PATH"; then
  echo "FAIL: no fired event in log"
  cat "$CLAUDE_AUTO_RETRY_LOG_PATH" 2>/dev/null || echo "(no log)"
  exit 1
fi
echo "  PASS"

echo "Test 2: --status renders"
out=$(python3 "$ENGINE" --status)
echo "$out" | grep -q "PENDING" || { echo "FAIL: no PENDING"; exit 1; }
echo "$out" | grep -q "RECENT" || { echo "FAIL: no RECENT"; exit 1; }
echo "  PASS"

echo "Test 3: orphan cleanup"
mkdir -p "$CLAUDE_AUTO_RETRY_PENDING_DIR"
echo '{"pid":99999,"pane_id":"%99","fires_at":"1990-01-01T00:00:00+00:00"}' \
  > "$CLAUDE_AUTO_RETRY_PENDING_DIR/99999.json"
TMUX_PANE="$TMUX_PANE" bash -c "echo '$EVT' | python3 '$ENGINE' --hook"
if [ -f "$CLAUDE_AUTO_RETRY_PENDING_DIR/99999.json" ]; then
  echo "FAIL: orphan was not cleaned up"
  ls -la "$CLAUDE_AUTO_RETRY_PENDING_DIR"
  exit 1
fi
echo "  PASS"

echo "All integration tests passed."
