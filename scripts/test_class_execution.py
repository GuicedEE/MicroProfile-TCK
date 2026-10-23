import unittest
from run_classes import aggregate, selections


class ClassExecutionTests(unittest.TestCase):
    def test_empty_execution_is_not_success(self):
        with self.assertRaises(ValueError): aggregate({'id':'empty'},[],0)

    def test_all_candidates_selected_including_nested(self):
        self.assertEqual(['A','A$Nested'],selections({}, {'candidateClasses':[{'name':'A$Nested'},{'name':'A'}]}))

    def test_factory_retains_upstream_factory_selection(self):
        self.assertEqual(['Factory'],selections({'factory':'Factory'},{'candidateClasses':[]}))

    def test_official_group_selection_cannot_be_overridden(self):
        for suite in [{'officialSelection':'cdi-lite groups'}, {'signature':'annotations.sig'}]:
            with self.assertRaises(ValueError): selections(suite, {'candidateClasses':[]})

    def test_timeout_cannot_be_hidden_by_other_classes_passing(self):
        rows=[]
        for name,status in [('A','PASSED_DIAGNOSTIC'),('B','TIMED_OUT')]:
            rows.append(dict(selectedClass=name,status=status,exitCode=int(status=='TIMED_OUT'),elapsedSeconds=1,
                             counts={'passed':int(name=='A'),'failed':0,'skipped':0},
                             cases=[dict(classname=name,name='test',status='passed',report='TEST-A.xml')] if name=='A' else [],
                             issues=[],command=['mvn']))
        result=aggregate({'id':'suite'},rows,2)
        self.assertEqual('TIMED_OUT',result['status'])
        self.assertEqual(['A','B'],result['selectedClasses'])
        self.assertEqual('classes/A/surefire/TEST-A.xml',result['cases'][0]['report'])
        self.assertEqual(2,len(result['classResults']))


if __name__=='__main__': unittest.main()
