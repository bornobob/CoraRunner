from subprocess import Popen, PIPE, STDOUT
from os import listdir, path
from pathlib import Path
from json import dumps, loads
from time import time
from re import compile
from sys import argv
from argparse import ArgumentParser


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
        configurations = self.get_configurations(**self.configs)
        files = listdir(self.test_files_path)
        for conf_idx, config in enumerate(configurations):
            for file_idx, file in enumerate(files):
                full_path = path.join(self.test_files_path, file)
                analysis_res = self.analyse(config, full_path)
                result.append({'file': full_path, 'config': config.__dict__, 'result': analysis_res.__dict__})
                print(f'[{conf_idx}/{len(configurations)}] [{file_idx}/{len(files)}] - Processed: {full_path}')
            with open(self.output_file, 'w') as f:
                f.write(dumps(result))


def get_argparser():
    parser = ArgumentParser()
    parser.add_argument('settings', type=str, metavar='<settings file>', help='Settings .json file')
    parser.add_argument('testdir', type=str, metavar='<test file directory>', help='Directory with test files')
    parser.add_argument('resultfile', type=str, metavar='<result file>', help='Resulting .json file')
    return parser


def check_valid_args(settings_file, test_dir, result_file):
    if not Path(settings_file).exists():
        print('Settings file does not exist, aborting...')
        return False
    if not Path(test_dir).exists():
        print('Test files directory does not exist, aborting...')
        return False
    if Path(result_file).exists():
        print('Output file already exists, aborting...')
        return False
    return True


if __name__ == '__main__':
    arguments = get_argparser().parse_args()
    if not check_valid_args(arguments.settings, arguments.testdir, arguments.resultfile):
        exit(1)
    else:
        CoraRunner(arguments.settings, arguments.testdir, arguments.resultfile).do_analysis()
