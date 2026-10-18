from unittest import mock

import src.utils.power as power


class TestPreventSystemSleep:
    def test_noop_on_non_windows(self, monkeypatch):
        monkeypatch.setattr(power.sys, "platform", "linux")
        with power.prevent_system_sleep(enabled=True, reason="build"):
            pass

    def test_calls_windows_api_on_enter_and_exit(self, monkeypatch):
        monkeypatch.setattr(power.sys, "platform", "win32")
        calls = []

        class _Kernel32:
            @staticmethod
            def SetThreadExecutionState(value):
                calls.append(value)
                return 1

        monkeypatch.setattr(
            power.ctypes,
            "windll",
            mock.Mock(kernel32=_Kernel32()),
            raising=False,
        )

        with power.prevent_system_sleep(enabled=True, reason="build"):
            pass

        assert calls == [
            power.ES_CONTINUOUS | power.ES_SYSTEM_REQUIRED,
            power.ES_CONTINUOUS,
        ]
