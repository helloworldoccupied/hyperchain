"""Tests for XiaotianQuan Guard Layer (Layer 1)."""
import pytest

from hyperchain.guards import GuardRegistry, Verdict, guard, BUILTIN_GUARDS
from hyperchain.errors import GuardBlockedError


class TestVerdict:
    def test_allow(self):
        v = Verdict.allow()
        assert v.allowed is True
        assert v.reason == ""
        assert v.guard_name == ""

    def test_block(self):
        v = Verdict.block("dangerous command")
        assert v.allowed is False
        assert v.reason == "dangerous command"


class TestGuardRegistry:
    def test_register_and_check(self):
        reg = GuardRegistry()

        @reg.register("bash")
        def no_rm(ctx: dict) -> Verdict:
            if "rm -rf" in ctx.get("command", ""):
                return Verdict.block("rm -rf is forbidden")
            return Verdict.allow()

        blocked = reg.check("bash", {"command": "rm -rf /"})
        assert blocked.allowed is False
        assert "rm -rf" in blocked.reason

        allowed = reg.check("bash", {"command": "ls"})
        assert allowed.allowed is True

    def test_multiple_guards_all_must_pass(self):
        reg = GuardRegistry()

        @reg.register("bash")
        def guard_a(ctx: dict) -> Verdict:
            return Verdict.allow()

        @reg.register("bash")
        def guard_b(ctx: dict) -> Verdict:
            return Verdict.block("guard_b says no")

        result = reg.check("bash", {"command": "anything"})
        assert result.allowed is False
        assert result.guard_name == "guard_b"

    def test_no_guards_allows(self):
        reg = GuardRegistry()
        result = reg.check("bash", {"command": "echo hi"})
        assert result.allowed is True

    def test_enforce_raises_on_block(self):
        reg = GuardRegistry()

        @reg.register("bash")
        def blocker(ctx: dict) -> Verdict:
            return Verdict.block("nope")

        with pytest.raises(GuardBlockedError) as exc_info:
            reg.enforce("bash", {"command": "x"})
        assert "nope" in str(exc_info.value)

    def test_enforce_passes_on_allow(self):
        reg = GuardRegistry()

        @reg.register("bash")
        def allower(ctx: dict) -> Verdict:
            return Verdict.allow()

        # Should not raise
        reg.enforce("bash", {"command": "echo hello"})


class TestBuiltInGuards:
    def _make_registry_with_builtins(self) -> GuardRegistry:
        reg = GuardRegistry()
        for event, fn in BUILTIN_GUARDS:
            reg.register_fn(event, fn)
        return reg

    def test_destructive_command_guard_rm(self):
        reg = self._make_registry_with_builtins()
        result = reg.check("bash", {"command": "rm -rf /"})
        assert result.allowed is False

    def test_destructive_command_guard_force_push(self):
        reg = self._make_registry_with_builtins()
        result = reg.check("bash", {"command": "git push --force"})
        assert result.allowed is False

    def test_destructive_command_guard_safe(self):
        reg = self._make_registry_with_builtins()
        result = reg.check("bash", {"command": "echo hello"})
        assert result.allowed is True

    def test_push_to_feature_branch_allowed(self):
        reg = self._make_registry_with_builtins()
        result = reg.check("bash", {"command": "git push origin feature/my-branch"})
        assert result.allowed is True


class TestGuardDecorator:
    def test_guard_sets_attributes(self):
        @guard("bash", tool="Bash")
        def my_guard(ctx: dict) -> Verdict:
            return Verdict.allow()

        assert my_guard._guard_event == "bash"
        assert my_guard._guard_tool == "Bash"

    def test_guard_without_tool(self):
        @guard("pre_tool")
        def my_guard(ctx: dict) -> Verdict:
            return Verdict.allow()

        assert my_guard._guard_event == "pre_tool"
        assert my_guard._guard_tool is None
