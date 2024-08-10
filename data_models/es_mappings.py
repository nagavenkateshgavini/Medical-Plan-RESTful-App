INDEX_NAME = 'plans'
INDEX_MAPPING = {
  "mappings": {
    "properties": {
      "objectId": {
        "type": "keyword"
      },
      "org": {
        "type": "keyword"
      },
      "objectType": {
        "type": "keyword"
      },
      "planType": {
        "type": "keyword"
      },
      "creationDate": {
        "type": "date"
      },
      "deductible": {
        "type": "double"
      },
      "copay": {
        "type": "double"
      },
      "name": {
        "type": "text"
      },
      "join_field": {
        "type": "join",
        "relations": {
          "plan": ["planCostShares", "linkedPlanServices"],
          "linkedPlanServices": ["linkedService", "planserviceCostShares"]
        }
      }
    }
  }
}
