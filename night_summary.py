import markdown
import jinja2
from weasyprint import HTML, CSS
from argparse import ArgumentParser
from sqlalchemy import create_engine
import yaml
import pandas as pd
from plots import plot_runtype, plot_sources, plot_run_timeline
from datetime import datetime, timedelta
import os


def connect_to_database(user, password, host, database):
    spec = 'mysql+pymysql://{user}:{password}@{host}/{database}'
    return create_engine(spec.format(
        user=user,
        password=password,
        host=host,
        database=database
    ))


def read_run(night, db):
    query = (
        ' SELECT fNight,fRunID,fSourceName,fOnTime,fRunTypeName,fRunStart,fRunStop'
        ' FROM RunInfo'
        ' LEFT JOIN Source'
        ' ON RunInfo.fSourceKEY = Source.fSourceKEY'
        ' LEFT JOIN RunType'
        ' ON RunInfo.fRunTypeKEY = RunType.fRunTypeKEY'
        ' WHERE fNight = {}'.format(night)
    )
    runs = pd.read_sql(query, db, parse_dates=['fRunStart', 'fRunStop'])
    return runs


def load_template(filename):
    with open(filename) as f:
        return jinja2.Template(f.read())


def html2pdf(html, outputfile, stylesheets=None):

    document = HTML(string=html)

    with open(outputfile, 'wb') as f:
        document.write_pdf(f, stylesheets=stylesheets)


parser = ArgumentParser()
parser.add_argument('--night', '-n', dest='night', default=None)
parser.add_argument('--config', '-c', dest='config', default='config.yaml')
parser.add_argument('--outputfile', '-o', dest='outputfile', default=None)


def build_summary(outputfile, template_file, db, night=None, stylesheets=None):

    if night is None:
        night = (datetime.today() - timedelta(days=2)).strftime('%Y%m%d')

    template = load_template(template_file)

    runs = read_run(night, db)

    os.makedirs('build', exist_ok=True)

    plot_run_timeline(runs, 'build/runs.svg')

    md = template.render(
        night=night,
        run_plot='build/runs.svg',
    )

    html = markdown.markdown(md, extensions=['markdown.extensions.tables'])
    document = HTML(string=html, base_url='.')

    outputfile = outputfile or 'fact_summary_{}.pdf'.format(night)
    document.write_pdf(outputfile,  stylesheets=stylesheets)


def main():
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    db = connect_to_database(**config)

    style = CSS('style.css')

    build_summary(
        args.outputfile,
        template_file='template.md',
        night=args.night,
        db=db,
        stylesheets=[style],
    )


if __name__ == '__main__':
    main()
