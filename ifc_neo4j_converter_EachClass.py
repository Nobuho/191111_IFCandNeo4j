import ifcopenshell
import sys
from py2neo import Graph, Node
import time
import os

neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j")
neo4j_password=os.getenv("NEO4J_PASSWORD", "neo4j")
neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687")
print (neo4j_uri,neo4j_username, neo4j_password)
def typeDict(key):
#    f = ifcopenshell.file()
    value = f.create_entity(key).wrapped_data.get_attribute_names()
    return value


start = time.time()  # Culculate time to process


ifc_path = "ifc_files/ronen_Structural.ifc"
#ifc_path = "ifc_files/20210125Prova.ifc"
start = time.time()  # Culculate time to process
print("Start!")
print(time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(time.ctime())))
log1 = str(time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(time.ctime()))) + " Start "


nodes = []
edges = []

f = ifcopenshell.open(ifc_path)
for el in f:
    if el.is_a() == "IfcOwnerHistory":
        continue
    tid = el.id()
    cls = el.is_a()
    pairs = []
    keys = []
    try:
        keys = [x for x in el.get_info() if x not in ["type", "id", "OwnerHistory"]]
    except RuntimeError:
        # we actually can't catch this, but try anyway
        pass
    for key in keys:
        val = el.get_info()[key]
        if any(hasattr(val, "is_a") and val.is_a(thisTyp)
               for thisTyp in ["IfcBoolean", "IfcLabel", "IfcText", "IfcReal"]):
            val = val.wrappedValue
        if val and type(val) is tuple and type(val[0]) in (str, bool, float, int):
            val = ",".join(str(x) for x in val)
        if type(val) not in (str, bool, float, int):
            continue
        pairs.append((key, val))
    nodes.append((tid, cls, pairs))

    for i in range(len(el)):
        try:
            el[i]
        except RuntimeError as e:
            if str(e) != "Entity not found":
                print("ID", tid, e, file=sys.stderr)
            continue
        if isinstance(el[i], ifcopenshell.entity_instance):
            if el[i].is_a() == "IfcOwnerHistory":
                continue
            if el[i].id() != 0:
                # edges.append({"from":tid, "to":el[i].id(), "reltype":typeDict(cls)[i]})
                # edges.append((tid, el[i].id(), typeDict(cls)[i]))
                edges.append((tid, cls, el[i].id(), el[i].is_a(), typeDict(cls)[i]))
                continue
        try:
            iter(el[i])
        except TypeError:
            continue
        # destinations = [
        #     x.id() for x in el[i] if isinstance(
        #         x, ifcopenshell.entity_instance)]
        # for connectedTo in destinations:
        #     # edges.append({"from": tid, "to": connectedTo, "reltype": typeDict(cls)[i]})
        #     edges.append((tid, connectedTo, typeDict(cls)[i]))
        destinations = [
            x.id() for x in el[i] if isinstance(
                x, ifcopenshell.entity_instance)]
        destinations_cls = [
            x.is_a() for x in el[i] if isinstance(
                x, ifcopenshell.entity_instance)]
        for (connectedTo, connectedTo_cls) in zip(destinations, destinations_cls):
            edges.append((tid, cls, connectedTo, connectedTo_cls, typeDict(cls)[i]))

if len(nodes) == 0:
    print("no nodes in file", file=sys.stderr)
    sys.exit(1)


print("List creat prosess done. Take for ", round(time.time() - start))
print(time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(time.ctime())))
log2 = str(round(time.time() - start)) + "sec.\n" + \
    str(time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(time.ctime()))) + " List creat prosess done"

# Initialize neo4j database
graph = Graph( uri=neo4j_uri,auth=(neo4j_username, neo4j_password))  # http://localhost:7474
graph.delete_all()

for node in nodes:
    nId, cls, pairs = node
    one_node = Node(cls, nid=nId)
    for k, v in pairs:
        one_node[k] = v
    graph.create(one_node)

# Index create process
# ifc_classes = set([i[2] for i in edges])
# for cl in ifc_classes:
#     graph.run("CREATE INDEX ON :{:s}(nid)".format(cl))

print("Node creat prosess done. Take for ", round(time.time() - start))
print(time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(time.ctime())))
log2 = str(round(time.time() - start)) + "sec.\n" + \
    str(time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(time.ctime()))) + " Node creat prosess done"

# query_rel = """
# MATCH (a)
# WHERE a.nid = {:d}
# MATCH (b)
# WHERE b.nid = {:d}
# CREATE (a)-[:{:s}]->(b)
# """

# for (nId1, nId2, relType) in edges:
#     graph.run(query_rel.format(nId1, nId2, relType))

query_rel = """
MATCH (a:{cls1})
WHERE a.nid = {id1}
MATCH (b:{cls2})
WHERE b.nid = {id2}
CREATE (a)-[:{relType}]->(b)
"""

for (id1, cls1, id2, cls2, relType) in edges:
    graph.run(query_rel.format(cls1=cls1, cls2=cls2, id1=id1, id2=id2, relType=relType))
print("All done. Take for ", round(time.time() - start))
print(time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(time.ctime())))
log3 = str(round(time.time() - start)) + "sec.\n" + \
    str(time.strftime("%Y/%m/%d %H:%M:%S", time.strptime(time.ctime()))) + " All done"

#with open("log.text", mode="a") as f:
#    f.write(ifc_path + "\n")
#    f.write("Nodes_" + str(len(nodes)) + " ,Edges_" + str(len(edges)) + "\n")
#    f.write(log1 + "\n")
#    f.write(log2 + "\n")
#    f.write(log3 + "\n\n")
