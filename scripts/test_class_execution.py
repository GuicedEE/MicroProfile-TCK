import unittest
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from run_classes import aggregate, selections, split_cdi_xml


class ClassExecutionTests(unittest.TestCase):
    def test_cdi_partition_preserves_groups_listeners_and_parameters(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'official.xml'
            source.write_text('<suite name="CDI"><listeners><listener class-name="Listener"/></listeners>'
                              '<test name="Lite"><parameter name="key" value="value"/><groups><run>'
                              '<exclude name="cdi-full"/><exclude name="se"/></run></groups>'
                              '<packages><package name="org.jboss.cdi.tck.tests.*"/></packages></test></suite>')
            paths=split_cdi_xml(source,['A','B'],root)
            original=ET.parse(source)
            for name,path in paths.items():
                tree=ET.parse(path)
                self.assertEqual(ET.tostring(original.find('listeners')),ET.tostring(tree.find('listeners')))
                self.assertEqual(ET.tostring(original.find('test/groups')),ET.tostring(tree.find('test/groups')))
                self.assertEqual(ET.tostring(original.find('test/parameter')),ET.tostring(tree.find('test/parameter')))
                self.assertEqual([name],[c.get('name') for c in tree.findall('test/classes/class')])
                self.assertIsNone(tree.find('test/packages'))
            self.assertIsNotNone(ET.parse(source).find('test/packages'))

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
