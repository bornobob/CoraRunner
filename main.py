from subprocess import Popen, PIPE, STDOUT
from os import walk
from os.path import join as path_join
from pathlib import Path
from json import dumps, loads
from time import time
from re import compile
from sys import argv


class AnalysisResult:
    def __init__(self, result_type, cora_time, cpu_time, error=None):
        self.result_type = result_type
        self.cora_time = cora_time
        self.cpu_time = cpu_time
        self.error = error


class Configuration:
    def __init__(self, technique, semi_unifier, max_unfoldings, timing, augment):
        self.technique = technique
        self.semi_unifier = semi_unifier
        self.max_unfoldings = max_unfoldings
        self.timing = timing
        self.augment = augment

    def to_commandline_arguments(self):
        return ['-t', self.technique,
                '-u', str(self.max_unfoldings),
                '-a', str(self.augment),
                '--su', self.semi_unifier,
                '--timeout', str(self.timing)]


class CoraRunner:
    def __init__(self, settings_path, test_files_path, output_file):
        self.RESULT_TYPE_REGEX = compile(r'Result type: ([a-zA-Z]+)')
        self.TIME_TAKEN_REGEX = compile(r'Time taken: ([0-9]+)ms')
        self.test_files_path = test_files_path
        self.java_path, self.cora_path, self.configs = self.parse_settings(settings_path)
        self.output_file = output_file

    @staticmethod
    def parse_settings(settings_path):
        with open(settings_path, 'r') as f:
            settings = loads(f.read())
            return settings['java-path'], settings['cora-path'], settings['configs']

    @staticmethod
    def remove_newlines(line):
        return line.replace('\n', '').replace('\r', '')

    @staticmethod
    def get_configurations(techniques, semi_unifiers, max_unfoldings, timings, augment):
        configurations = []
        for t in techniques:
            for s in semi_unifiers:
                for u in max_unfoldings:
                    for a in augment:
                        for c in timings:
                            configurations.append(Configuration(t, s, u, c, a))
        return configurations

    def analyse(self, configuration, trs_file):
        arguments = configuration.to_commandline_arguments()
        start_time = time()
        p = Popen([self.java_path, '-jar', self.cora_path, *arguments, '-i', trs_file], stdout=PIPE, stderr=STDOUT)
        lines = list(p.stdout)
        cpu_time = (time() - start_time) * 1000
        return self.parse_analysis_result([self.remove_newlines(str(line, 'utf8')) for line in lines], cpu_time)

    def parse_analysis_result(self, lines, cpu_time):
        match = self.RESULT_TYPE_REGEX.match(lines[0])
        if match:
            time_match = self.TIME_TAKEN_REGEX.match(lines[-1])
            if time_match:
                return AnalysisResult(match[1], time_match[1], cpu_time)
            else:
                return AnalysisResult('ERROR', 0, cpu_time, error='Time match failed')
        else:  # error occurred
            return AnalysisResult('ERROR', 0, cpu_time, error=lines[0])

    def do_analysis(self):
        result = []
        for config in self.get_configurations(**self.configs):
            for root, _, files in walk(self.test_files_path):
                for file in files:
                    path = path_join(root, file)
                    analysis_res = self.analyse(config, path)
                    result.append({'file': path, 'config': config.__dict__, 'result': analysis_res.__dict__})
                    print('Processed: {}'.format(path))
                break
        with open(self.output_file, 'w') as f:
            f.write(dumps(result))


def get_arguments():
    if len(argv) != 4:
        print('Call as "python {} <settings file> <test file directory> <result file>", aborting...'.format(argv[0]))
        exit(1)

    if not Path(argv[1]).exists():
        print('Settings file does not exist, aborting...')
        exit(1)

    if not Path(argv[2]).exists():
        print('Test files directory does not exist, aborting...')
        exit(1)

    if Path(argv[3]).exists():
        print('Output file already exists, aborting...')
        exit(1)

    return argv[1], argv[2], argv[3]


if __name__ == '__main__':
    settings_file, test_files_dir, output = get_arguments()
    CoraRunner(settings_file, test_files_dir, output).do_analysis()
