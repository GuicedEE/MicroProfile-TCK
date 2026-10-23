"""Regression checks for evidence classification, independent of any runtime implementation."""
import contextlib
import io
import json
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import run_tcks


class ReportingTests(unittest.TestCase):
    def test_timeout_remains_explicit_and_stops_its_process_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            process=Mock(pid=12345,wait=Mock(side_effect=[subprocess.TimeoutExpired('mvn',1),0,0]))
            with patch.object(run_tcks,'ROOT',Path(directory)), \
                    patch.object(run_tcks.shutil,'which',return_value='mvn'), \
                    patch.object(run_tcks.subprocess,'Popen',return_value=process), \
                    patch.object(run_tcks.subprocess,'run') as stop, \
                    patch.object(run_tcks.os,'killpg',create=True) as kill, contextlib.redirect_stdout(io.StringIO()):
                result=run_tcks.execute({'id':'timeout'},Path(directory),1,18080)
            self.assertEqual('TIMED_OUT',result['status'])
            self.assertEqual(124,result['exitCode'])
            if run_tcks.os.name=='nt': self.assertEqual(['taskkill','/PID','12345','/T','/F'],stop.call_args.args[0])
            else: self.assertEqual(2,kill.call_count)

    def classify(self, xml, code=0):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)

            def start(*args, **kwargs):
                reports = run/'example'/'surefire'
                reports.mkdir()
                for name, contents in xml.items():
                    (reports/name).parent.mkdir(parents=True, exist_ok=True)
                    (reports/name).write_text(contents)
                return Mock(wait=Mock(return_value=code))

            with patch.object(run_tcks, 'ROOT', run), patch.object(run_tcks.shutil, 'which', return_value='mvn'), \
                    patch.object(run_tcks.subprocess, 'Popen', side_effect=start), contextlib.redirect_stdout(io.StringIO()):
                result = run_tcks.execute({'id': 'example'}, run, 10, 18080)
            self.assertEqual(result, json.loads((run/'example'/'result.json').read_text()))
            return result

    def test_missing_reports_are_blocked_even_with_zero_exit(self):
        self.assertEqual('BLOCKED_NO_RESULTS', self.classify({})['status'])

    def test_parse_failure_cannot_be_hidden_by_a_passing_report(self):
        result = self.classify({'TEST-good.xml': '<testsuite><testcase name="ok"/></testsuite>', 'TEST-bad.xml': '<broken'})
        self.assertEqual('FAILED', result['status'])
        self.assertEqual('REPORT_PARSE', result['issues'][0]['kind'])

    def test_skipped_tests_are_incomplete(self):
        self.assertEqual('INCOMPLETE_SKIPS', self.classify({'TEST-a.xml': '<testsuite><testcase><skipped/></testcase></testsuite>'})['status'])

    def test_failure_keeps_cause_and_signature_even_with_zero_exit(self):
        result = self.classify({'TEST-a.xml': '<testsuite><testcase classname="A" name="test"><failure type="Error">wrapper\nCaused by: Missing provider</failure></testcase></testsuite>'})
        self.assertEqual('FAILED', result['status'])
        self.assertEqual('Caused by: Missing provider', result['cases'][0]['message'])
        self.assertTrue(result['cases'][0]['issue'].startswith('TCK-'))

    def test_nonzero_exit_overrides_passing_cases(self):
        self.assertEqual('FAILED', self.classify({'TEST-a.xml': '<testsuite><testcase/></testsuite>'}, code=1)['status'])

    def test_pass_is_explicitly_diagnostic(self):
        self.assertEqual('PASSED_DIAGNOSTIC', self.classify({'TEST-a.xml': '<testsuite><testcase/></testsuite>'})['status'])

    def test_testng_duplicate_reports_are_not_counted_twice(self):
        xml = '<testsuite><testcase classname="A" name="test"/></testsuite>'
        result = self.classify({'TEST-a.xml': xml, 'junitreports/TEST-a.xml': xml})
        self.assertEqual(1, result['counts']['passed'])


if __name__ == '__main__':
    unittest.main()
