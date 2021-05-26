# export ANSIBLE_CALLBACK_PLUGINS={Directory of Playbook}
# export ANSIBLE_STDOUT_CALLBACK=progression
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback.default import CallbackModule as CallbackModule_default
import re,os,datetime

DOCUMENTATION = '''
    callback: progression
    callback_type: stdout
    requirements:
      - set as main display callback
    short_description: Ansible screen output tracks the tasks headers and status to resume from last failed point.
    version_added: "2.0"
    extends_documentation_fragment:
      - default_callback
    description:
        - This callback does the same as the default except it has an additional tracker functions which helps to log the tasks status in a seperate file.
'''

class CallbackModule(CallbackModule_default):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''
    PEER_IP = ""
    LOCAL_IP = ""
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'progression'
    #host_var

    def tracker(self, result, status):
        task = result._task
        host = result._host.get_name()
        self.logger(host, task, status)

    def logger(self, host, task, status):
        #name = task.split(' ',maxsplit=1)
        name = str(task).replace('TASK','').replace(': ','')

        if(name=="Gathering Facts"):
           return 0

        if(str(self.PEER_IP) == str(host)):
          node = 'node2'
        elif(str(self.LOCAL_IP) == str(host)):
          node = 'node1'
        else:
          node = str(host)

        f = open('playbook.inprogress', 'r')
        entries = f.read()
        f.close()
        sample_entry = node + ':{' + name + '}:'
        if(status == "skipped"):
          final_entry=""
        else:
          final_entry = node + ':{' + name + '}:' + status

        if re.search(sample_entry+'(failed|started)', entries, re.IGNORECASE):
          r = re.compile(sample_entry+'(failed|started)', re.IGNORECASE)
          final_entries = r.sub(final_entry, entries)
        else:
          final_entries = entries + '\n' + final_entry
        final_entries = os.linesep.join([s for s in final_entries.splitlines() if s])
        file = open('playbook.inprogress', 'w')
        file.write(final_entries)
        file.close()

    def v2_runner_on_failed(self, result, ignore_errors=False):
        #print(result._host.get_name(),result._task,"failed")
        if(ignore_errors == True):
          self.tracker(result, "failure_ignored")
        else:
          self.tracker(result, "failed")
        super(CallbackModule,self).v2_runner_on_failed(result, ignore_errors)

    def v2_runner_on_ok(self, result):
        #print(result._host.get_name(),result._task,"ok")
        self.tracker(result, "ok")
        super(CallbackModule,self).v2_runner_on_ok(result)

    def v2_playbook_on_task_start(self, task, is_conditional):
        ct = datetime.datetime.now()
        ts = ct.strftime('%Y-%m-%d %H:%M:%S')
        self._task_start(task, prefix='['+ts+']')

    def v2_runner_on_start(self, host, task):
        #print(host,task,"started")
        self.logger(host, task, "started")
        super(CallbackModule,self).v2_runner_on_start(host, task)

    def v2_runner_on_skipped(self, result):
        #print(result._host.get_name(),result._task,"skipped")
        self.tracker(result, "skipped")
        super(CallbackModule,self).v2_runner_on_skipped(result)

    def v2_runner_item_on_skipped(self, result):
        super(CallbackModule,self).v2_runner_item_on_skipped(result)

    def v2_runner_retry(self, result):
        task_name = result.task_name or result._task
        msg = "FAILED - RETRYING: %s (%d retries left)." % (task_name, result._result['retries'] - result._result['attempts'])
        if self._run_is_verbose(result, verbosity=2):
            msg += "Result was: %s" % self._dump_results(result._result)
        self._display.display(msg, color=C.COLOR_DEBUG)

    def v2_playbook_on_play_start(self, play):
        variable_manager = play.get_variable_manager()
        extra_vars = variable_manager.extra_vars
        #print("NODE1:"+str(extra_vars['local_ip'])+"++++++++++++++NODE2:"+str(extra_vars['peer_ip']))
        self.PEER_IP = extra_vars['peer_ip']
        self.LOCAL_IP = extra_vars['local_ip']
        super(CallbackModule,self).v2_playbook_on_play_start(play)

    def v2_runner_retry(self, result):
        super(CallbackModule,self).v2_runner_retry(result)

    def v2_playbook_on_notify(self, handler, host):
        super(CallbackModule,self).v2_playbook_on_notify(handler, host)