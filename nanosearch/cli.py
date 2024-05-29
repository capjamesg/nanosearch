import click
from . import NanoSearchBM25, REMOVE_ALL_SEPARATORS
from flask import Flask, render_template, request

@click.group()
def cli():
    pass

@click.command("serve")
@click.option("--index", default=None)
@click.option("--sitemap", default=None)
def search(index, sitemap):
    if index is None:
        engine = NanoSearchBM25().from_sitemap(sitemap, title_transforms=REMOVE_ALL_SEPARATORS)
        engine.to_nanosearch_json("data.json")
    else:
        engine = NanoSearchBM25().from_nanosearch_json(index)
    
    if index is None and sitemap is None:
        raise ValueError("You must provide either a sitemap or a Nanosearch index.")

    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def search():
        if "search" not in request.args:
            return render_template("index.html", query="", results=[])

        query = request.args.get("search", "")
        results = engine.search(query, n = 10)

        return render_template("index.html", query=query, results=results, results_count=len(results))

    app.run(port=5001)

cli.add_command(search)