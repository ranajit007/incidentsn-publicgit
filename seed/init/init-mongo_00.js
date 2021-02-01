db = db.getSiblingDB('service_now');
db.createUser({
    user: "incidentUser",
    pwd: "redhat",
    roles: [
        {
            role: "readWrite",
            db: "service_now"
        },
        {
          role: "dbAdmin",
          db: "service_now"
        }
    ]
});
db.createCollection("config");
db.createCollection("ProposedProcedure");
db.createCollection("incidents_ewm_full");
db.setLogLevel(1)
