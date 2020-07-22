import sys
import requests
import lxml.html
import rdflib
import re
from rdflib import Graph, Literal, RDF, URIRef, XSD
import datetime

uri_pref = "http://example.org/"
wiki_pref = "http://en.wikipedia.org"


# ________________________Part 1 - Parser functions ________________________


def parse_input(raw_input):
    # Strip <> from the input.
    text_input = raw_input.replace("<", '').replace(">", '').replace("?", '')
    text_input = text_input.lower()
    text_input_tokens = text_input.split()
    if len(text_input_tokens) < 3 or len(text_input_tokens) > 11:
        return 0, None, None
    if "who is the president" in text_input:
        entity = ' '.join(str(elem) for elem in text_input_tokens[5:]).replace(" ", "_")
        relation = text_input_tokens[3]
        return 1, relation, entity
    if "who is the prime minister of" in text_input:
        entity = ' '.join(str(elem) for elem in text_input_tokens[6:]).replace(" ", "_")
        relation = text_input_tokens[3] + "_" + text_input_tokens[4]
        return 2, relation, entity
    if "what is the population of" in text_input:
        entity = ' '.join(str(elem) for elem in text_input_tokens[5:]).replace(" ", "_")
        relation = text_input_tokens[3] + "_of"
        return 3, relation, entity
    if "what is the area of" in text_input:
        entity = ' '.join(str(elem) for elem in text_input_tokens[5:]).replace(" ", "_")
        relation = text_input_tokens[3] + "_of"
        return 4, relation, entity
    if "what is the government of" in text_input:
        entity = ' '.join(str(elem) for elem in text_input_tokens[5:]).replace(" ", "_")
        relation = text_input_tokens[3] + "_of"
        return 5, relation, entity
    if "what is the capital of" in text_input:
        entity = ' '.join(str(elem) for elem in text_input_tokens[5:]).replace(" ", "_")
        relation = text_input_tokens[3] + "_of"
        return 6, relation, entity
    if "when was the president of" in text_input:
        entity = ' '.join(str(elem) for elem in text_input_tokens[5:-1]).replace(" ", "_")
        relation = text_input_tokens[3]
        return 7, relation, entity
    if "when was the prime minister of" in text_input:
        entity = ' '.join(str(elem) for elem in text_input_tokens[6:-1]).replace(" ", "_")
        relation = text_input_tokens[3] + "_" + text_input_tokens[4]
        return 8, relation, entity
    if "who is" in text_input and len(text_input_tokens) <= 5:
        entity = ' '.join(str(elem) for elem in text_input_tokens[2:]).replace(" ", "_")
        relation = "entity"
        return 9, relation, entity
    else:
        return 0,0,0
	


def create_query(index, relation, entity):
    if index < 7:
        query = "SELECT ?p \
                WHERE {\
                     <%s> <%s> ?p .\
                }" % (uri_pref + entity, uri_pref + relation)
    elif index == 7 or index == 8:
        query = "SELECT ?p \
                WHERE {\
                     <%s> <%s> ?x . ?x <%s> ?p\
                }" % (uri_pref + entity, uri_pref + relation, uri_pref + "born_at")

    else:
        query = "SELECT ?c ?r \
                WHERE {\
                    <%s> ?r ?c. \
                }" % (uri_pref + entity)

    return query


def fix_result(index, result):
    if len(result) == 0:
        return "no data"
    else:
        if index == 1 or index == 2 or index == 6:
            for elem in result:
                fixed_result = elem[0]
                fixed_result = fixed_result.replace("http://example.org/", '').replace("_", ' ')
                return fixed_result
        elif index == 3:  # Population
            for elem in result:
                try:
                    fixed_result = elem[0][:elem[0].index("(")]
                    return fixed_result
                except ValueError:
                    fixed_result = elem[0]
                    return fixed_result
        elif index == 4:  # Area
            for elem in result:
                fixed_result = elem[0].replace("\u2013", "-").replace("_", " ")
            return fixed_result
        elif index == 5:  # Goverment
            for elem in result:
                if elem[0][len(elem[0]) - 1] == "]":
                    fixed_result = elem[0].replace("\u2013", "-").replace("_", " ")[:-3]
                else:
                    fixed_result = elem[0].replace("\u2013", "-").replace("_", " ")
            return fixed_result
        elif index == 7 or index == 8:
            for elem in result:
                for fmt in ('%d %B %Y', '%B %d, %Y'):
                    try:
                        fixed_result = datetime.datetime.strptime(elem[0].replace("_", " "), fmt).date()
                        return fixed_result
                    except ValueError:
                        if fmt == '%B %d, %Y':
                            fixed_result = elem[0].replace("_", " ")
                            return fixed_result
                        else:
                            pass
        elif index == 9:
            for elem in result:
                if elem[1][19:] == "president_of":
                    fixed_result = elem[0]
                    fixed_result = "President of " + fixed_result.replace("http://example.org/", '').replace("_", ' ')
                    return fixed_result
                elif elem[1][19:] == "pm_of":
                    fixed_result = elem[0]
                    fixed_result = "Prime minister of " + fixed_result.replace("http://example.org/", '').replace("_",
                                                                                                                  ' ')
                    return fixed_result
            else:
                return "error"


def run_query(raw_input):
    parser_result = parse_input(raw_input)
    if parser_result[0] == 0:
        print("Incorrect query")
    else:
        data_graph = rdflib.Graph()  # Init empty graph
        data_graph.parse("ontology.nt", format="nt")  # Load .nt file
        query = create_query(parser_result[0], parser_result[1], parser_result[2])
        result = data_graph.query(query)
        print(fix_result(parser_result[0], result))


# ________________________Part 2 - Infrormation Extraction ________________________


#  relations
president_of = rdflib.URIRef(uri_pref + 'president_of')
president = rdflib.URIRef(uri_pref + 'president')
prime_minister_of = rdflib.URIRef(uri_pref + 'prime_minister_of')
prime_minister = rdflib.URIRef(uri_pref + 'prime_minister')
population_of = rdflib.URIRef(uri_pref + 'population_of')
government_of = rdflib.URIRef(uri_pref + 'government_of')
capital_of = rdflib.URIRef(uri_pref + 'capital_of')
area_of = rdflib.URIRef(uri_pref + 'area_of')
born_at = rdflib.URIRef(uri_pref + 'born_at')


def create_ontology(tittle):
    g = rdflib.Graph()
    countries_links = get_all_countries()
    for country in countries_links:
        extract_country_info(country, g)
    g.serialize(tittle, format="nt")


# extract birth date from wiki page (if possible) and convert it to numeric format string
# @returns string (date) or None
def get_birth_date(url):
    dic_month = {"January": '01', "February": '02', "March": '03', "April": '04', "May": '05', "June": '06',
                 "July": '07', "August": '08', 'September': '09', "October": '10', "November": '11', "December": '12'}
    r = requests.get(wiki_pref + url)
    doc = lxml.html.fromstring(r.content)
    date = doc.xpath("//table[contains(@class,'infobox')]/tbody/tr/th[text() = 'Born']/ancestor::tr/td/text()")
    if len(date) > 0:
        date = date[0].replace(",", "").split(' ')
        if len(date) == 3:
            x = 0 if date[0].isdigit() else 1
            bd = date[2] + '-' + dic_month[date[1 - x]] + '-' + date[x]
            return bd
    return None


# extract all countries url's from the main wiki table
# @returns list of url's
def get_all_countries():
    countries = []
    r = requests.get("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)")
    doc = lxml.html.fromstring(r.content)
    countries_table = doc.xpath("//tbody[contains(tr/th[1]/text(), 'Country')]/tr[position() > 1]")
    for row in countries_table:
        link = row.xpath("./td[1]//a/@href")
        if len(link) > 0:
            countries.append(link[0])
    return countries


# gets current ontology graph and country's wiki url, extract relevant info from the wiki page and update the ontology
def extract_country_info(url, graph):
    r = requests.get(wiki_pref + url)
    doc = lxml.html.fromstring(r.content)
    country = rdflib.URIRef(uri_pref + url.split("/")[-1])
    info_box = doc.xpath("//table[contains(./@class, 'infobox')]")[0]

    population = info_box.xpath("//tr[th[.//text() = 'Population']]/following-sibling::tr[1]/td//text()[1]")
    if len(population) > 0:
        population = ' '.join(population).strip().split()[0]
        graph.add((country, population_of, Literal(population)))

    area = info_box.xpath(".//tr[contains(.//text(), 'Area')]/following-sibling::tr[1]/td[1]/text()")
    if len(area) == 0:
        area = info_box.xpath(".//tr[contains(.//text(), 'Area')]/td[1]/text()")
    if len(area) > 0:
        area = area[0].split()[0] + "_km2"
        graph.add((country, area_of, Literal(area)))

    government = info_box.xpath("//tr/th/a[text() = 'Government']/ancestor::tr/td//a/text()")
    if len(government) == 0:
        government = info_box.xpath("//tr/th[text() = 'Government']/ancestor::tr/td//a/text()")
    if len(government) > 0:
        for i in government:
            if any(char.isdigit() for char in i):
                government.remove(i)
        government = "_".join(government).replace(" ", "_")
        graph.add((country, government_of, Literal(government)))

    capital = info_box.xpath("//tr/th[text() = 'Capital']/ancestor::tr/td//a/@href")
    if len(capital) > 0:
        capital = capital[0].split("/")[-1]
        graph.add((country, capital_of, Literal(capital)))

    prime_minister_link = info_box.xpath("//tr[th//a[text() = 'Prime Minister']]/td//a/@href")
    if len(prime_minister_link) > 0:
        pm = rdflib.URIRef(uri_pref + prime_minister_link[0].split("/")[-1])
        pm_link = prime_minister_link[0]
        date = get_birth_date(pm_link)
        graph.add((pm, prime_minister_of, country))
        graph.add((country, prime_minister, pm))
        if date:
            graph.add((pm, born_at, Literal(date, datatype=XSD.date)))

    president_link = info_box.xpath("//tr[th//a[text() = 'President']]/td//a/@href")
    if len(president_link) > 0:
        pr = rdflib.URIRef(uri_pref + president_link[0].split("/")[-1])
        president_link = president_link[0]
        date = get_birth_date(president_link)
        graph.add((pr, president_of, country))
        graph.add((country, president, pr))
        if date:
            graph.add((pr, born_at, Literal(date, datatype=XSD.date)))




# ________________________Run ________________________



cmd = sys.argv[1]
inpt = sys.argv[2]

if cmd == "create":
    create_ontology(inpt)

if cmd == "question":
    run_query(inpt)

