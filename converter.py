from xml.etree import ElementTree
from pathlib import Path
from argparse import ArgumentParser
from os import listdir, mkdir, path


class TRS:
    def __init__(self, rules, signature):
        self.rules = rules
        self.signature = signature

    def __str__(self):
        signature = 'Signature:\n - ' + '\n - '.join(str(s) for s in self.signature)
        rules = 'Rules:\n - ' + '\n - '.join(str(r) for r in self.rules)
        return '{}\n\n{}'.format(signature, rules)


class Rule:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return '{} -> {}'.format(str(self.left), str(self.right))


class Variable:
    def __init__(self, name, sort):
        self.name = name
        self.sort = sort

    def __str__(self):
        return self.name


class FunctionSymbol:
    def __init__(self, name, signature):
        self.name = name
        self.signature = signature

    def is_constant(self):
        return len(self.signature) == 1

    def __str__(self):
        sort = ' -> '.join(self.signature)
        return '{} :: {}'.format(self.name, sort)


class Function:
    def __init__(self, symbol, arguments):
        self.symbol = symbol
        self.arguments = arguments

    def __str__(self):
        arguments = ', '.join(str(a) for a in self.arguments)
        if self.symbol.is_constant():
            return self.symbol.name
        else:
            return '{}({})'.format(self.symbol.name, arguments)


class XMLParser:
    def __init__(self, xml_path):
        self.path = xml_path
        self.xml_root = self.parse_xml()
        self.signature = self.parse_signature()
        self.rules = self.parse_rules()

    def parse_xml(self):
        tree = ElementTree.parse(self.path)
        root = tree.getroot()
        return root

    def parse_signature(self):
        signature = []
        for func_symbol in self.xml_root.findall('./trs/signature/funcsym'):
            name = func_symbol.find('name').text
            arity = int(func_symbol.find('arity').text) + 1
            signature.append(FunctionSymbol(name, ['a'] * arity))
        return signature

    def parse_rules(self):
        rules = []
        for rule in self.xml_root.findall('./trs/rules/rule'):
            left = self.parse_term(rule.find('lhs')[0])
            right = self.parse_term(rule.find('rhs')[0])
            rules.append(Rule(left, right))
        return rules

    def parse_term(self, xml_term):
        if xml_term.tag == 'var':
            return self.parse_variable(xml_term)
        elif xml_term.tag == 'funapp':
            return self.parse_func_app(xml_term)

    @staticmethod
    def parse_variable(xml_variable):
        return Variable(xml_variable.text, 'a')

    def parse_func_app(self, xml_funapp):
        name = xml_funapp.find('name').text
        func_symb = self.get_function_symbol(name)
        arguments = []
        for arg in xml_funapp.findall('./arg'):
            arguments.append(self.parse_term(arg[0]))
        return Function(func_symb, arguments)

    def get_function_symbol(self, name):
        for func_symb in self.signature:
            if func_symb.name == name:
                return func_symb

    def get_trs(self):
        return TRS(self.rules, self.signature)


class MSTRSWriter:
    def __init__(self, trs):
        self.trs = trs

    def write_to_file(self, outfile):
        if Path(outfile).exists():
            raise FileExistsError()
        else:
            with open(outfile, 'w') as f:
                f.write(self.generate_mstrs())

    def generate_mstrs(self):
        signature = self.generate_signature()
        rules = self.generate_rules()
        return '{}\n{}'.format(signature, rules)

    def generate_signature(self):
        func_symbols = []
        for func_symb in self.trs.signature:
            out_sort = func_symb.signature[-1]
            rest_sorts = ' '.join(func_symb.signature[:-1])
            func_symbols.append('{} {} -> {}'.format(func_symb.name, rest_sorts, out_sort))
        signature = '\n  '.join('({})'.format(x) for x in func_symbols)
        return '(SIG\n  {}\n)'.format(signature)

    def generate_rules(self):
        rules = '\n  '.join(str(r) for r in self.trs.rules)
        return '(RULES\n  {}\n)'.format(rules)


class Converter:
    def __init__(self, input_path, output_path, file_mode):
        self.input_path = input_path
        self.output_path = output_path
        self.file_mode = file_mode

    def convert(self):
        if self.file_mode:
            self.convert_single(self.input_path, self.output_path)
        else:
            self.convert_directory()

    def convert_directory(self):
        if not Path(self.output_path).exists():
            mkdir(self.output_path)
        for file in listdir(self.input_path):
            if file.endswith('.xml'):
                output_file = path.join(self.output_path, Path(file).stem + '.mstrs')
                self.convert_single(path.join(self.input_path, file), output_file)

    @staticmethod
    def convert_single(input_file, output_file):
        try:
            trs = XMLParser(input_file).get_trs()
            MSTRSWriter(trs).write_to_file(output_file)
        except Exception as e:
            print('ERROR: {}: {}'.format(input_file, str(e)))


def create_argparser():
    parser = ArgumentParser(description='Convert .xml Term rewriting system files into .mstrs files.')
    parser.add_argument('mode', choices=['dir', 'file'], help='Choose dir or file depending on what the input is')
    parser.add_argument('input', type=str, help='The input file/directory')
    parser.add_argument('output', type=str, help='The output file/directory')
    return parser


if __name__ == '__main__':
    args = create_argparser().parse_args()
    Converter(args.input, args.output, args.mode == 'file').convert()
