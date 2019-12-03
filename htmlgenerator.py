from dominate.tags import *
from dominate.document import document
from dominate.util import raw
from json import loads
from collections import defaultdict
from os.path import basename
from sys import argv
from pathlib import Path


class Result:
    def __init__(self, file, config, result):
        self.file = file
        self.config = config
        self.result = result


class HTMLGenerator:
    def __init__(self, results_file, output_file):
        self.results_file = results_file
        self.output_file = output_file
        self.results = self.get_results()
        self.results_by_file = self.sort_results()
        self.configs = self.get_configs()

    def get_results(self):
        result = []
        with open(self.results_file, 'r') as f:
            results = loads(f.read())
            for res in results:
                result.append(Result(res['file'], res['config'], res['result']))
        return result

    def sort_results(self):
        result = defaultdict(list)
        for res in self.results:
            result[res.file].append(res)
        return result

    def get_configs(self):
        result = set()
        for res in self.results:
            result.add(frozenset(res.config.items()))
        return list(dict(r) for r in result)

    def get_result(self, config, file):
        for result in self.results_by_file[file]:
            if result.config == config:
                return result.result
        return None

    @staticmethod
    def config_to_html(config):
        return 'Technique: {}<br/>Semi-Unifier: {}<br/>Max unfoldings: {}<br/>Augment TRS: {}<br/>Timeout: {}'.format(
            config['technique'], config['semi_unifier'], config['max_unfoldings'], config['augment'], config['timing']
        )

    @staticmethod
    def get_timings_from_result(result):
        return '{:.2f} / {:.2f}'.format(float(result['cpu_time']) / 1000, float(result['cora_time']) / 1000)

    def get_nr_success(self, config):
        result = 0
        for results in self.results_by_file.values():
            for res in results:
                if res.config == config and res.result['result_type'] in ['NONTERMINATES']:
                    result += 1
        return result

    def create_html_page(self):
        d = document(title='Cora Results')
        with d:
            with d.head:
                link(rel='stylesheet', href='style.css')
            h1('RESULTS')
            with table(id='results'):
                with thead():
                    head_row = tr()
                    head_row.add(th('Benchmark'))
                    for c in self.configs:
                        head_row.add(th(raw(self.config_to_html(c))))
                with tbody():
                    for file in sorted(list(self.results_by_file.keys())):
                        row = tr()
                        row += td(a(basename(file), href='file:///{}'.format(file)))
                        for c in self.configs:
                            result = self.get_result(c, file)
                            if result:
                                row += td(
                                    result['result_type'],
                                    br(),
                                    self.get_timings_from_result(result),
                                    cls=result['result_type'].lower()
                                )
                            else:
                                row += td()
                with tfoot():
                    foot = tr()
                    foot.add(th('Total:'))
                    for c in self.configs:
                        foot.add(th('{} / {}'.format(
                            self.get_nr_success(c),
                            len(list(self.results_by_file.keys()))
                        )))
        return d.render()

    def generate_html(self):
        outfile = self.output_file
        if not outfile.endswith('.html'):
            outfile += '.html'
        with open(outfile, 'w') as f:
            f.write(self.create_html_page())


if __name__ == '__main__':
    if len(argv) != 3:
        print('Call as "python {} <results file> <output file>", aborting...'.format(argv[0]))
        exit(1)

    if not Path(argv[1]).exists():
        print('Results file does not exist, aborting...')
        exit(1)

    if Path(argv[2]).exists():
        print('Output file already exists, aborting...')
        exit(1)

    HTMLGenerator(argv[1], argv[2]).generate_html()
