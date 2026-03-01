# Scenarios: Inventory Check & Store Lookup

**Feature**: F-04 / F-05

---

## Scenario S-04-01: Successful inventory check

```
Given the MCP server is running
And HD_API_KEY is set
When the client calls check_inventory with item_id "202038841" and store_id "6902"
Then the response contains in_stock (boolean)
And the response contains quantity (integer >= 0)
And when in_stock is true, aisle and bay fields are present
```

---

## Scenario S-04-02: Item out of stock

```
Given the MCP server is running
When the client calls check_inventory with a known out-of-stock item and valid store_id
Then in_stock is false
And quantity is 0
And no error is returned
```

---

## Scenario S-04-03: Inventory check using zip code instead of store_id

```
Given the MCP server is running
When the client calls check_inventory with item_id "202038841" and zip_code "30301"
Then the server resolves the nearest store to zip 30301
And returns inventory for that store
And the response includes the resolved store_id
```

---

## Scenario S-04-04: Invalid store ID

```
Given the MCP server is running
When the client calls check_inventory with item_id "202038841" and store_id "99999"
Then the response contains error true
And the error code is "STORE_NOT_FOUND"
```

---

## Scenario S-05-01: Successful store lookup

```
Given the MCP server is running
And HD_API_KEY is set
When the client calls find_store with zip_code "30301"
Then the response contains a list of at least 1 store
And each store has: store_id, name, address, phone, hours, distance_miles
And stores are ordered by distance ascending
```

---

## Scenario S-05-02: No stores within radius

```
Given the MCP server is running
When the client calls find_store with zip_code "99999" and radius 5
Then the response contains an empty stores list
And no error is returned
```

---

## Scenario S-05-03: Missing zip code

```
Given the MCP server is running
When the client calls find_store without a zip_code parameter
Then the response contains error true
And the error code is "INVALID_PARAMS"
```
