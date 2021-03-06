"""
ShakerExecutor class:
    - shaker framework execution class
"""
import ConfigParser
import os

from oslo_config import cfg
from oslo_log import log as logging

from harbinger.common.utils import Utils
from harbinger.executors.base import BaseExecutor

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class ShakerExecutor(BaseExecutor):
    def __init__(self, framework, environment, options):
        super(ShakerExecutor, self).__init__(framework, environment, options)
        self.cfg_file_name = self.framework.name + ".cfg"
        self.cfg_full_path = os.path.join(self.inputs_dir, self.cfg_file_name)
        self.results_json_path = os.path.join(self.outputs_dir,
                                              "shaker-results.json")
        self.config = ConfigParser.RawConfigParser()

    def setup(self):
        super(ShakerExecutor, self).setup()

        image_name = Utils.hierarchy_lookup(self, 'image')
        image_exists = self.image.check_image(image_name)

        if image_exists is False:
            self.create_image()
            self.image.upload_image(image_name, 'qcow2', 'bare')

        self.create_cfg_file()
        self._exec_cmd("shaker --config-file " + self.cfg_full_path)

    def collect_scenario_tests(self):
        tests_list = self.framework.tests
        scenario = ""
        for i, test in enumerate(tests_list):
            path = os.path.join(CONF.DEFAULT.files_dir, "frameworks",
                                self.framework.name,
                                CONF.shaker.test_paths, test)
            if i + 1 == len(tests_list):
                scenario += path
            else:
                scenario += path + ", "

        return scenario

    def add_extras_options(self):
        for key, value in self.framework.extras.iteritems():
            self.config.set("DEFAULT", str(key), value)

    def create_cfg_file(self):
        if hasattr(self.framework, 'extras'):
            self.add_extras_options()

        username = Utils.hierarchy_lookup(self, 'username')
        password = Utils.hierarchy_lookup(self, 'password')
        project_name = Utils.hierarchy_lookup(self, 'project')
        flavor_name = Utils.hierarchy_lookup(self, 'flavor_name')
        image_name = Utils.hierarchy_lookup(self, 'image')
        output = self.results_json_path
        scenario = self.collect_scenario_tests()
        server_endpoint = Utils.hierarchy_lookup(self, 'server_endpoint')
        external_net = Utils.hierarchy_lookup(self, 'external_network')

        self.config.set("DEFAULT", "os_username", username)
        self.config.set("DEFAULT", "os_password", password)
        self.config.set("DEFAULT", "os_project_name", project_name)
        self.config.set("DEFAULT", "flavor_name", flavor_name)
        self.config.set("DEFAULT", "image_name", image_name)
        self.config.set("DEFAULT", "output", output)
        self.config.set("DEFAULT", "scenario", scenario)
        self.config.set("DEFAULT", "server_endpoint", server_endpoint)
        self.config.set("DEFAULT", "external_net", external_net)

        with open(self.cfg_full_path, 'wb') as configfile:
            self.config.write(configfile)

    def create_image(self):
        Utils.source_openrc(self)
        self._exec_cmd("shaker-image-builder")
