import unittest

from experience import Demo, OBSERVATION_CONSENT


class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.demo = Demo()
        self.employee = self.demo.employee_session
        self.admin = self.demo.admin_session
        self.call = self.demo.employee_request
        self.control = self.demo.admin_request

    def test_status_clarification_and_disconnect(self):
        status = self.call(self.employee, "status")
        self.assertEqual(status.state, "Awaiting clarification")
        self.assertEqual(status.clarification, "Which fictional inbox: Cedar or Maple?")
        self.assertEqual(self.demo.adapter.dispatched, [])
        with self.assertRaises(ValueError):
            self.call(self.employee, "answer", "invalid")
        self.assertEqual(self.call(self.employee, "answer", "Cedar").state, "Running")
        self.demo.adapter.connected = False
        self.demo.tick()
        self.assertEqual(self.call(self.employee, "status").state, "Status unknown")
        self.assertEqual(self.demo.adapter.dispatched, [])

    def test_pause_settles_and_resume_does_not_replay(self):
        self.call(self.employee, "answer", "Cedar")
        self.demo.tick()
        status = self.call(self.employee, "pause")
        self.assertEqual((status.state, status.in_flight), ("Pausing", "Cedar: open"))
        with self.assertRaises(ValueError):
            self.call(self.employee, "resume")
        self.demo.tick()
        self.assertEqual(self.call(self.employee, "status").state, "Paused")
        self.demo.tick()
        self.assertEqual(self.demo.adapter.dispatched, ["Cedar: open"])
        self.call(self.employee, "resume")
        for _ in range(3):
            self.demo.tick()
        self.assertEqual(
            self.demo.adapter.dispatched, ["Cedar: open", "Cedar: summarize"]
        )
        self.assertEqual(self.call(self.employee, "status").state, "Completed")

    def test_stop_drops_queue_and_cannot_resume(self):
        self.call(self.employee, "answer", "Maple")
        self.demo.tick()
        status = self.call(self.employee, "stop")
        self.assertEqual((status.state, status.in_flight), ("Stopped", "Maple: open"))
        self.demo.tick()
        self.demo.tick()
        self.assertEqual(self.call(self.employee, "status").state, "Stopped")
        with self.assertRaises(ValueError):
            self.call(self.employee, "resume")
        self.assertEqual(self.demo.adapter.dispatched, ["Maple: open"])

    def test_employee_cannot_enable_observation_even_after_consent(self):
        self.call(self.employee, "grant-observation")
        for session in (self.employee, None, object()):
            with self.subTest(session=session):
                for operation in ("enable-observation", "observe"):
                    with self.assertRaises(PermissionError):
                        self.control(session, operation)
        with self.assertRaises(PermissionError):
            self.call(self.employee, "enable-observation")
        self.assertFalse(self.call(self.employee, "status").observation_active)

    def test_admin_observation_is_opt_in_visible_read_only_and_revocable(self):
        self.assertIn("this run only", OBSERVATION_CONSENT)
        with self.assertRaises(PermissionError):
            self.control(self.admin, "enable-observation")
        self.call(self.employee, "grant-observation")
        self.control(self.admin, "enable-observation")
        self.assertTrue(self.call(self.employee, "status").observation_active)
        self.assertEqual(self.control(self.admin, "observe"), "Awaiting clarification")
        self.call(self.employee, "pause")
        with self.assertRaises(PermissionError):
            self.control(self.admin, "resume")
        self.assertEqual(self.call(self.employee, "status").state, "Paused")
        self.call(self.employee, "revoke-observation")
        self.assertFalse(self.call(self.employee, "status").observation_active)
        with self.assertRaises(PermissionError):
            self.control(self.admin, "observe")
        self.call(self.employee, "grant-observation")
        self.control(self.admin, "enable-observation")
        self.call(self.employee, "stop")
        with self.assertRaises(PermissionError):
            self.control(self.admin, "observe")


if __name__ == "__main__":
    unittest.main()
