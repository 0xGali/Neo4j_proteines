from flask import Flask, jsonify, render_template
from neo4j import GraphDatabase


app = Flask(__name__)

@app.route("/")
def home():
    return render_template("base.html")

# Configuration de la connexion à Neo4j
uri = "neo4j://127.0.0.1:7687"
user = "neo4j"
password = "password"
driver = GraphDatabase.driver(uri, auth=(user, password))

def get_db_session():
    return driver.session()

@app.route('/proteins/<entry>/similar/<float:seuil>', methods=['GET'])
def get_similar_proteins(entry,seuil):
    with get_db_session() as session:
        query = """
        MATCH (p1:Proteine {Entry: $entry})-[r:SIMILAR]->(p2:Proteine)
        WHERE r.jaccard > $seuil AND p1.Entry <> p2.Entry
        RETURN p2.Entry AS neighbor, r.jaccard AS jaccard_index
        ORDER BY jaccard_index DESC
        """
        result = session.run(query, entry=entry, seuil = float(seuil))
        return jsonify([dict(record) for record in result])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)