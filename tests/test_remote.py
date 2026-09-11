# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: Intra2net AG and aexpect contributors
# Author: Plamen Dimitrov <plamen.dimitrov@intra2net.com>
#
# selftests pylint: disable=C0111,C0111,W0613,R0913,E1101,C0301

import unittest.mock

from aexpect import remote
from aexpect.client import RemoteSession

mock = unittest.mock


class TestRemoteFunctions(unittest.TestCase):

    def setUp(self):
        session_read = mock.MagicMock()
        session_read.return_value = 12, remote.PROMPT_LINUX
        session_patch = mock.patch.object(
            RemoteSession, "read_until_last_line_matches", session_read
        )
        session_patch.start()
        self.addCleanup(session_patch.stop)
        expect_patch = mock.patch("aexpect.remote.Expect")
        self.expect = expect_patch.start()
        self.addCleanup(expect_patch.stop)

    def test_handle_prompts(self):
        output = remote.handle_prompts(
            RemoteSession(), "user", "pass", remote.PROMPT_LINUX
        )
        self.assertEqual(output, remote.PROMPT_LINUX)

    def test_remote_login(self):
        session = remote.remote_login(
            "ssh", "127.0.0.1", 22, "user", "pass", remote.PROMPT_LINUX
        )
        self.assertEqual(
            session.command,
            "ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -p 22"
            " -o PreferredAuthentications=password user@127.0.0.1",
        )

    def test_wait_for_login(self):
        session = remote.wait_for_login(
            "ssh", "127.0.0.1", 22, "user", "pass", remote.PROMPT_LINUX
        )
        self.assertEqual(
            session.command,
            "ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -p 22"
            " -o PreferredAuthentications=password user@127.0.0.1",
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_remote_copy(self, mock_remote_copy):
        remote.remote_copy("cp a b", ["pass"])
        mock_remote_copy.assert_called_once_with(
            mock.ANY,
            ["pass"],
            600,
            300,
            "scp",
        )
        self.expect.assert_called_once_with(
            r"cp a b",
            output_func=None,
            output_params=(),
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_scp_to_remote(self, mock_remote_copy):
        remote.scp_to_remote(
            "127.0.0.1", 22, "user", "pass", "/local/path", "/remote/path"
        )
        mock_remote_copy.assert_called_once_with(
            mock.ANY, ["pass"], 600, 300, "scp"
        )
        self.expect.assert_called_once_with(
            r"scp -r -v -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PreferredAuthentications=password  -P 22 /local/path user@\[127.0.0.1\]:/remote/path",
            output_func=None,
            output_params=(),
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_scp_from_remote(self, mock_remote_copy):
        remote.scp_from_remote(
            "127.0.0.1", 22, "user", "pass", "/remote/path", "/local/path"
        )
        mock_remote_copy.assert_called_once_with(
            mock.ANY, ["pass"], 600, 300, "scp"
        )
        self.expect.assert_called_once_with(
            r"scp -r -v -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PreferredAuthentications=password  -P 22 user@\[127.0.0.1\]:/remote/path /local/path",
            output_func=None,
            output_params=(),
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_scp_between_remotes(self, mock_remote_copy):
        remote.scp_between_remotes(
            "src_host",
            "dst_host",
            22,
            "src_pass",
            "dst_pass",
            "src_user",
            "dst_user",
            "/src/path",
            "/dst/path",
        )
        mock_remote_copy.assert_called_once_with(
            mock.ANY, ["src_pass", "dst_pass"], 600, 300, "scp"
        )
        self.expect.assert_called_once_with(
            r"scp -r -v -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PreferredAuthentications=password  -P 22 src_user@\[src_host\]:/src/path dst_user@\[dst_host\]:/dst/path",
            output_func=None,
            output_params=(),
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_rsync_to_remote(self, mock_remote_copy):
        remote.rsync_to_remote(
            "127.0.0.1", 22, "user", "pass", "/local/path", "/remote/path"
        )
        mock_remote_copy.assert_called_once_with(
            mock.ANY, ["pass"], 600, 300, "rsync"
        )
        self.expect.assert_called_once_with(
            r"rsync -r -avz -e 'ssh -Tp 22 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'  /local/path user@127.0.0.1:/remote/path",
            output_func=None,
            output_params=(),
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_rsync_from_remote(self, mock_remote_copy):
        remote.rsync_from_remote(
            "127.0.0.1", 22, "user", "pass", "/remote/path", "/local/path"
        )
        mock_remote_copy.assert_called_once_with(
            mock.ANY, ["pass"], 600, 300, "rsync"
        )
        self.expect.assert_called_once_with(
            r"rsync -r -avz -e 'ssh -Tp 22 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'  user@127.0.0.1:/remote/path /local/path",
            output_func=None,
            output_params=(),
        )


class TestRemoteCopyRetry(unittest.TestCase):

    def setUp(self):
        copy_patch = mock.patch("aexpect.remote._remote_copy")
        self.copy = copy_patch.start()
        self.addCleanup(copy_patch.stop)
        expect_patch = mock.patch("aexpect.remote.Expect")
        self.expect = expect_patch.start()
        self.addCleanup(expect_patch.stop)
        sleep_patch = mock.patch("aexpect.remote.time.sleep")
        self.sleep = sleep_patch.start()
        self.addCleanup(sleep_patch.stop)
        self.retry_errors = (
            remote.TransferTimeoutError("Transfer stalled"),
            remote.AuthenticationTimeoutError("Login stalled"),
            remote.ExpectTimeoutError(["password"], "No response"),
            remote.TransferFailedError(1, "Connection reset"),
            remote.SCPError("Copy failed", "CONNECTION lost"),
            remote.RsyncError("Copy failed", "TIMEOUT"),
        )

    def assert_attempts(self, attempts):
        self.assertEqual(self.copy.call_count, attempts)
        self.assertEqual(self.expect.call_count, attempts)
        self.assertEqual(
            self.expect.return_value.__exit__.call_count, attempts
        )
        self.assertEqual(
            self.sleep.call_args_list, [mock.call(1)] * (attempts - 1)
        )

    def test_success_does_not_retry(self):
        remote.remote_copy("scp source destination", ["pass"], attempts=3)
        self.assert_attempts(1)

    def test_default_attempt_does_not_retry(self):
        self.copy.side_effect = remote.TransferTimeoutError("Transfer stalled")
        with self.assertRaises(remote.TransferTimeoutError):
            remote.remote_copy("scp source destination", ["pass"])
        self.assert_attempts(1)

    def test_transient_errors_retry_until_success(self):
        for error in self.retry_errors:
            with self.subTest(error=error):
                for mocked in (self.copy, self.expect, self.sleep):
                    mocked.reset_mock()
                self.copy.side_effect = [error, None]
                remote.remote_copy(
                    "scp source destination", ["pass"], attempts=3
                )
                self.assert_attempts(2)

    def test_exhausted_attempts_raise_last_error(self):
        for error in self.retry_errors:
            for attempts in (1, 3):
                with self.subTest(error=error, attempts=attempts):
                    for mocked in (self.copy, self.expect, self.sleep):
                        mocked.reset_mock()
                    self.copy.side_effect = [
                        remote.TransferTimeoutError("Earlier failure")
                    ] * (attempts - 1) + [error]
                    with self.assertRaises(type(error)) as raised:
                        remote.remote_copy(
                            "scp source destination",
                            ["pass"],
                            attempts=attempts,
                        )
                    self.assertIs(raised.exception, error)
                    self.assert_attempts(attempts)

    def test_permanent_errors_do_not_retry(self):
        for error in (
            remote.TransferFailedError(1, "Permission denied"),
            remote.SCPError("Copy failed", "No such file"),
            remote.RsyncError("Copy failed", "No such file"),
            remote.AuthenticationError("Login failed", "Permission denied"),
            ValueError("Invalid transfer"),
        ):
            with self.subTest(error=error):
                for mocked in (self.copy, self.expect, self.sleep):
                    mocked.reset_mock()
                self.copy.side_effect = error
                with self.assertRaises(type(error)) as raised:
                    remote.remote_copy(
                        "scp source destination", ["pass"], attempts=3
                    )
                self.assertIs(raised.exception, error)
                self.assert_attempts(1)

    def test_wrappers_preserve_attempts(self):
        args = ("host", 22, "user", "pass", "/source", "/destination")
        session = mock.Mock(
            host="host", port=22, username="user", password="pass"
        )
        cases = [
            (remote.scp_to_remote, args),
            (remote.scp_from_remote, args),
            (remote.rsync_to_remote, args),
            (remote.rsync_from_remote, args),
            (
                remote.scp_between_remotes,
                (
                    "src",
                    "dst",
                    22,
                    "pass",
                    "pass",
                    "user",
                    "user",
                    "/source",
                    "/destination",
                ),
            ),
            (remote.scp_to_session, (session, "/source", "/destination")),
            (remote.scp_from_session, (session, "/source", "/destination")),
        ]
        for client in ("scp", "rsync"):
            for method in (remote.copy_files_to, remote.copy_files_from):
                cases.append(
                    (
                        method,
                        (
                            "host",
                            client,
                            "user",
                            "pass",
                            22,
                            "/source",
                            "/destination",
                        ),
                    )
                )
        for method, args in cases:
            with self.subTest(method=method, args=args):
                for mocked in (self.copy, self.expect, self.sleep):
                    mocked.reset_mock()
                self.copy.side_effect = [
                    remote.TransferTimeoutError("Transfer stalled"),
                    remote.TransferTimeoutError("Transfer stalled again"),
                    None,
                ]
                method(*args, attempts=3)
                self.assert_attempts(3)


class TestRSSCopyRetry(unittest.TestCase):

    def setUp(self):
        self.args = (
            "host",
            "rss",
            "user",
            "pass",
            22,
            "/source",
            "/destination",
        )
        self.cases = (
            (remote.copy_files_to, "FileUploadClient", "upload"),
            (remote.copy_files_from, "FileDownloadClient", "download"),
        )
        self.retry_errors = (
            (
                True,
                remote.rss_client.FileTransferConnectError(
                    "Connection failed"
                ),
            ),
            (
                False,
                remote.rss_client.FileTransferTimeoutError("Transfer stalled"),
            ),
            (
                False,
                remote.rss_client.FileTransferSocketError("Connection lost"),
            ),
        )
        sleep_patch = mock.patch("aexpect.remote.time.sleep")
        self.sleep = sleep_patch.start()
        self.addCleanup(sleep_patch.stop)

    def test_connection_and_transfer_retry_until_success(self):
        for method, client_class, operation in self.cases:
            for connection_failure, error in self.retry_errors:
                with self.subTest(client=client_class, error=error):
                    self.sleep.reset_mock()
                    first, second = mock.Mock(), mock.Mock()
                    getattr(first, operation).side_effect = error
                    with mock.patch.object(
                        remote.rss_client, client_class
                    ) as client:
                        client.side_effect = [
                            error if connection_failure else first,
                            second,
                        ]
                        method(*self.args, attempts=3)
                        self.assertEqual(client.call_count, 2)
                    getattr(second, operation).assert_called_once_with(
                        "/source", "/destination", 600
                    )
                    second.close.assert_called_once_with()
                    self.sleep.assert_called_once_with(1)

    def test_connection_and_transfer_attempts_exhausted(self):
        for method, client_class, operation in self.cases:
            for connection_failure, error in self.retry_errors:
                for attempts in (1, 3):
                    with self.subTest(
                        client=client_class,
                        error=error,
                        attempts=attempts,
                    ):
                        self.sleep.reset_mock()
                        with mock.patch.object(
                            remote.rss_client, client_class
                        ) as client:
                            if connection_failure:
                                client.side_effect = error
                            else:
                                getattr(
                                    client.return_value, operation
                                ).side_effect = error
                            with self.assertRaises(type(error)) as raised:
                                method(*self.args, attempts=attempts)
                            self.assertIs(raised.exception, error)
                            self.assertEqual(client.call_count, attempts)
                        self.assertEqual(
                            self.sleep.call_args_list,
                            [mock.call(1)] * (attempts - 1),
                        )

    def test_other_errors_do_not_retry(self):
        for method, client_class, operation in self.cases:
            for error in (
                remote.rss_client.FileTransferError("Transfer failed"),
                remote.rss_client.FileTransferNotFoundError("No such file"),
                remote.rss_client.FileTransferProtocolError("Invalid message"),
                remote.rss_client.FileTransferServerError("Permission denied"),
                TypeError("Invalid argument"),
                ValueError("Invalid value"),
            ):
                with self.subTest(client=client_class, error=error):
                    self.sleep.reset_mock()
                    with mock.patch.object(
                        remote.rss_client, client_class
                    ) as client:
                        transfer = getattr(client.return_value, operation)
                        transfer.side_effect = error
                        with self.assertRaises(type(error)) as raised:
                            method(*self.args, attempts=3)
                        self.assertIs(raised.exception, error)
                        client.assert_called_once_with("host", 22, None)
                        transfer.assert_called_once_with(
                            "/source", "/destination", 600
                        )
                    self.sleep.assert_not_called()


class TestTransferSessionCleanup(unittest.TestCase):

    def setUp(self):
        self.args = (
            "src",
            "dst",
            22,
            "pass",
            "pass",
            "user",
            "user",
            "/src/path",
            "/dst/path",
        )
        self.s_session = mock.Mock(spec=RemoteSession)
        self.d_session = mock.Mock(spec=RemoteSession)
        self.s_session.cmd_status_output.return_value = (0, "NCFT")
        self.s_session.cmd.return_value = "abc"
        self.d_session.cmd.return_value = "abc"
        self.s_session.cmd_output.return_value = "abc /src/path\nsendfile"
        self.d_session.cmd_output.return_value = "abc /dst/path"
        login_patch = mock.patch("aexpect.remote.remote_login")
        self.login = login_patch.start()
        self.addCleanup(login_patch.stop)
        self.login.side_effect = [self.s_session, self.d_session]
        sleep_patch = mock.patch("aexpect.remote.time.sleep")
        self.sleep = sleep_patch.start()
        self.addCleanup(sleep_patch.stop)

    def test_login_failure_closes_created_sessions(self):
        error = remote.LoginError("Login failed")
        for method in (
            remote.nc_copy_between_remotes,
            remote.udp_copy_between_remotes,
        ):
            for source_connected in (False, True):
                with self.subTest(method=method, source=source_connected):
                    self.s_session.reset_mock()
                    self.login.side_effect = (
                        [self.s_session, error]
                        if source_connected
                        else [error]
                    )
                    with self.assertRaises(remote.LoginError) as raised:
                        method(*self.args)
                    self.assertIs(raised.exception, error)
                    self.assertEqual(
                        self.s_session.close.call_count, int(source_connected)
                    )

    def test_nc_closes_only_created_sessions(self):
        for supply_source, supply_destination in (
            (False, False),
            (True, False),
            (False, True),
            (True, True),
        ):
            for status in (0, 1):
                with self.subTest(
                    source=supply_source,
                    destination=supply_destination,
                    status=status,
                ):
                    self.s_session.reset_mock()
                    self.d_session.reset_mock()
                    self.login.reset_mock()
                    self.login.side_effect = [
                        session
                        for session, supplied in (
                            (self.s_session, supply_source),
                            (self.d_session, supply_destination),
                        )
                        if not supplied
                    ]
                    self.s_session.cmd_status_output.return_value = (
                        status,
                        "NCFT",
                    )
                    kwargs = {
                        "s_session": self.s_session if supply_source else None,
                        "d_session": (
                            self.d_session if supply_destination else None
                        ),
                    }
                    if status:
                        with self.assertRaises(
                            remote.NetcatTransferFailedError
                        ):
                            remote.nc_copy_between_remotes(
                                *self.args, **kwargs
                            )
                    else:
                        self.assertTrue(
                            remote.nc_copy_between_remotes(
                                *self.args, **kwargs
                            )
                        )
                    self.assertEqual(
                        self.s_session.close.call_count, int(not supply_source)
                    )
                    self.assertEqual(
                        self.d_session.close.call_count,
                        int(not supply_destination),
                    )
                    self.assertEqual(
                        self.login.call_count,
                        int(not supply_source) + int(not supply_destination),
                    )

    def test_nc_retry_preserves_supplied_session(self):
        replacement = mock.Mock(spec=RemoteSession)
        self.login.side_effect = [self.d_session, replacement]
        self.s_session.cmd_status_output.side_effect = [
            (1, "NCFT"),
            (0, "NCFT"),
        ]
        self.assertTrue(
            remote.nc_copy_between_remotes(
                *self.args,
                s_session=self.s_session,
                check_sum=False,
                attempts=2,
            )
        )
        self.s_session.close.assert_not_called()
        self.d_session.close.assert_called_once_with()
        replacement.close.assert_called_once_with()
        self.assertEqual(self.login.call_count, 2)
        self.sleep.assert_called_once_with(1)

    def test_udp_success_closes_sessions(self):
        remote.udp_copy_between_remotes(*self.args)
        self.s_session.close.assert_called_once_with()
        self.d_session.close.assert_called_once_with()
        self.s_session.cmd_output_safe.assert_called_once_with(
            "killall sendfile"
        )

    def test_udp_stop_failure_closes_sessions(self):
        error = remote.UDPError("Cannot stop server")
        self.s_session.cmd_output_safe.side_effect = error
        with self.assertRaises(remote.UDPError) as raised:
            remote.udp_copy_between_remotes(*self.args)
        self.assertIs(raised.exception, error)
        self.s_session.close.assert_called_once_with()
        self.d_session.close.assert_called_once_with()

    def test_udp_retry_does_not_reuse_previous_sessions(self):
        error = remote.LoginError("Login failed")
        self.login.side_effect = [self.s_session, self.d_session, error]
        self.d_session.cmd_output_safe.side_effect = remote.UDPError(
            "Transfer failed"
        )
        with self.assertRaises(remote.LoginError) as raised:
            remote.udp_copy_between_remotes(*self.args, attempts=2)
        self.assertIs(raised.exception, error)
        self.s_session.close.assert_called_once_with()
        self.d_session.close.assert_called_once_with()
        self.sleep.assert_called_once_with(1)

    def test_source_close_failure_still_closes_destination(self):
        error = RuntimeError("Cannot close source")
        self.s_session.close.side_effect = error
        for method in (
            remote.nc_copy_between_remotes,
            remote.udp_copy_between_remotes,
        ):
            with self.subTest(method=method):
                self.s_session.reset_mock()
                self.d_session.reset_mock()
                self.login.side_effect = [self.s_session, self.d_session]
                with self.assertRaises(RuntimeError) as raised:
                    method(*self.args)
                self.assertIs(raised.exception, error)
                self.s_session.close.assert_called_once_with()
                self.d_session.close.assert_called_once_with()
