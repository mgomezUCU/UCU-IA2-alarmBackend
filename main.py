import pysmile as ps
from flask import Flask, request, jsonify
import pysmile_license
from flask_cors import CORS, cross_origin

app = Flask(__name__)

network = ps.Network()
network.read_file("alarmTest.xdsl")
network.update_beliefs()

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route("/ping")
def ping():
    return "pong"


def get_outcomes(handle, network, posteriors):
    return [
        {
            "id": network.get_outcome_id(handle, i),
            "probability": float(round(posteriors[i], 2))
        }
        for i in range(len(posteriors))
    ]


def is_diagnosis(node):
    if network.get_node_user_properties(node):
        return network.get_node_user_properties(node)[0].value == "diagnosis"


@app.route("/variables")
@cross_origin()
def variables():
    network.clear_all_evidence()
    network.update_beliefs()
    variables = []
    nodes = network.get_all_nodes()
    for handle in nodes:
        node_type = None
        node_summary = None
        node_id = network.get_node_id(handle)
        node_name = network.get_node_name(handle)
        posteriors = network.get_node_value(handle)
        if network.get_node_user_properties(handle):
            node_type = getattr(network.get_node_user_properties(handle)[0], 'value', None)
            node_summary = getattr(network.get_node_user_properties(handle)[1], 'value', None)
        outcomes = get_outcomes(handle, network, posteriors)
        variables.append({"id": node_id, "description": node_name,
                          "outcomes": outcomes, "type": node_type,
                          "summary": node_summary})
    return jsonify(variables)


@app.route("/diagnose", methods=['POST'])
@cross_origin()
def diagnose():
    network.clear_all_evidence()
    diseases = []
    data = request.json
    evidences = data['evidence']
    for evidence in evidences:
        variable_id = evidence['variable']
        outcome = evidence['outcome']
        if outcome:
            network.set_evidence(variable_id, outcome)
    network.update_beliefs()
    nodes = network.get_all_nodes()
    for handle in nodes:
        disease_id = network.get_node_id(handle)
        disease_name = network.get_node_name(handle)
        node_type = None
        if network.get_node_user_properties(handle):
            node_type = getattr(network.get_node_user_properties(handle)[0], 'value', None)
        posteriors = network.get_node_value(handle)
        outcomes = [{"id": network.get_outcome_id(handle, i),
                    "odds": float(round(posteriors[i], 2))} for i in range(len(posteriors))]
        diseases.append({"id": disease_id, "name": disease_name, "outcomes": outcomes, "type": node_type})
    return jsonify(diseases)


if __name__ == '__main__':
    app.run(port=8080)
