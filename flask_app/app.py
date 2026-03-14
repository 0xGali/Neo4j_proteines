from flask import Flask, jsonify, render_template
from neo4j import GraphDatabase


app = Flask(__name__)

@app.route("/")
def home():
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Proteine)
            OPTIONAL MATCH (p)-[r:SIMILAR]->(v:Proteine)
            WHERE r.jaccard >= $seuil
            RETURN p, collect(v) as voisins
        """, seuil=0.3)

        proteins = []
        for record in result:
            p = record["p"]
            voisins = record["voisins"]
            proteins.append({
                "Entry": p.get("Entry",""),
                "EntryName": p.get("EntryName",""),
                "InterPro": p.get("InterPro",""),
                "Sequence": p.get("Sequence",""),
                "ProteinNames" : p.get("ProteinNames",""),
                "voisins": [{"EntryName": v.get("EntryName","")} for v in voisins]
                })

    return render_template('base.html', proteins=proteins)

@app.route("/proteins/<seuil>", methods=['GET'])
def homeSeuil(seuil):
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Proteine)
            OPTIONAL MATCH (p)-[r:SIMILAR]->(v:Proteine)
            WHERE r.jaccard >= $seuil ORDER BY r.jaccard DESC
            RETURN p, collect(v) as voisins
        """, seuil=float(seuil))

        proteins = []
        for record in result:
            p = record["p"]
            voisins = record["voisins"]
            proteins.append({
                "Entry": p.get("Entry",""),
                "EntryName": p.get("EntryName",""),
                "InterPro": p.get("InterPro",""),
                "Sequence": p.get("Sequence",""),
                "ProteinNames" : p.get("ProteinNames",""),
                "voisins": [{"EntryName": v.get("EntryName","")} for v in voisins]
                })

    return render_template('base.html', proteins=proteins)

# Configuration de la connexion à Neo4j
uri = "neo4j://127.0.0.1:7687"
user = "neo4j"
password = "password"
driver = GraphDatabase.driver(uri, auth=(user, password))

def get_db_session():
    return driver.session()

@app.route('/protein/<entry>', methods=['GET'])
def protein(entry):
    with get_db_session() as session:
        query = """
        MATCH (p:Proteine {Entry:$entry})
        OPTIONAL MATCH (p)-[r:SIMILAR]->(v:Proteine)
        WHERE r.jaccard >= 0.3
        RETURN p,
        collect({voisin: v, jaccard: r.jaccard}) as voisins
        """
        result = session.run(query, entry=entry)
        record = result.single()
        if not record:
            return "Protéine non trouvée", 404

        p = record["p"]
        voisins_data = record["voisins"]

        # Formatage pour le template
        protein_data = {
            "Entry": p.get("Entry", ""),
            "EntryName": p.get("EntryName", ""),
            "ProteinNames": p.get("ProteinNames", ""),
            "InterPro": p.get("InterPro", ""),
            "Sequence": p.get("Sequence", ""),
            "voisins": [
                {
                    "Entry": v["voisin"].get("Entry", ""),
                    "EntryName": v["voisin"].get("EntryName", ""),
                    "jaccard": v["jaccard"]
                }
                for v in voisins_data if v["voisin"] is not None
            ]
        }

    return render_template('protein.html', protein=protein_data)

        

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)