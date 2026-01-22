#!/bin/bash
# 🧪 Test Script per Goal Notes Functionality

BASE_URL="http://localhost:5000/api"

echo "═════════════════════════════════════════════════════"
echo "🧪 Goal Notes Functionality - Test Suite"
echo "═════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Create Goal with Initial Note
echo -e "\n${BLUE}Test 1: Create Goal with Initial Note${NC}"
echo "POST $BASE_URL/goals"
curl -X POST "$BASE_URL/goals" \
  -H "Content-Type: application/json" \
  -d '{
    "ambito": "Reply",
    "titolo": "Aumentare fatturato Q1",
    "descrizione": "Incrementare il fatturato del 20%",
    "scadenza": "2025-03-31",
    "priorita": "high",
    "note": "Nota iniziale: strategie da implementare"
  }' | jq .

# Test 2: Get All Goals
echo -e "\n${BLUE}Test 2: Get All Goals (Active)${NC}"
echo "GET $BASE_URL/goals?status=active"
curl -s "$BASE_URL/goals?status=active" | jq .

# Test 3: Search Goal by Title
echo -e "\n${BLUE}Test 3: Search Goal by Title${NC}"
echo "GET $BASE_URL/goals/search?titolo=fatturato"
curl -s "$BASE_URL/goals/search?titolo=fatturato" | jq .

# Extract goal_id from search result for next tests
GOAL_ID=$(curl -s "$BASE_URL/goals/search?titolo=fatturato" | jq -r '.goals[0].goal_id' 2>/dev/null)

if [ ! -z "$GOAL_ID" ] && [ "$GOAL_ID" != "null" ]; then
    echo -e "${GREEN}Found goal ID: $GOAL_ID${NC}"
    
    # Test 4: Get Specific Goal
    echo -e "\n${BLUE}Test 4: Get Specific Goal${NC}"
    echo "GET $BASE_URL/goals?goal_id=$GOAL_ID"
    curl -s "$BASE_URL/goals?goal_id=$GOAL_ID" | jq .
    
    # Test 5: Add Note via PUT
    echo -e "\n${BLUE}Test 5: Add Note to Goal (Frontend Source)${NC}"
    echo "PUT $BASE_URL/goals"
    curl -X PUT "$BASE_URL/goals" \
      -H "Content-Type: application/json" \
      -d "{
        \"goal_id\": \"$GOAL_ID\",
        \"note\": \"Ho completato l'analisi di mercato e contattato 10 nuovi lead\",
        \"note_source\": \"frontend\"
      }" | jq .
    
    # Test 6: Add Another Note (Agent Source)
    echo -e "\n${BLUE}Test 6: Add Another Note (Agent Source)${NC}"
    echo "PUT $BASE_URL/goals"
    curl -X PUT "$BASE_URL/goals" \
      -H "Content-Type: application/json" \
      -d "{
        \"goal_id\": \"$GOAL_ID\",
        \"note\": \"Agente ha inviato email a 5 clienti potenziali\",
        \"note_source\": \"agent\"
      }" | jq .
    
    # Test 7: Update Goal Status with Note
    echo -e "\n${BLUE}Test 7: Update Goal Status + Add Note${NC}"
    echo "PUT $BASE_URL/goals"
    curl -X PUT "$BASE_URL/goals" \
      -H "Content-Type: application/json" \
      -d "{
        \"goal_id\": \"$GOAL_ID\",
        \"status\": \"active\",
        \"priority\": \"urgent\",
        \"note\": \"Aggiornata priorità a URGENTE - deadline si avvicina\",
        \"note_source\": \"frontend\"
      }" | jq .
    
    # Test 8: Get Goal with Updated Notes
    echo -e "\n${BLUE}Test 8: Get Goal with Complete Note History${NC}"
    echo "GET $BASE_URL/goals?goal_id=$GOAL_ID"
    curl -s "$BASE_URL/goals?goal_id=$GOAL_ID" | jq '.goals[0] | {
      goal_id,
      titolo,
      status,
      note_history: .note_history
    }'
    
    # Test 9: Add Note via POST (Alternative Endpoint)
    echo -e "\n${BLUE}Test 9: Add Note via POST Endpoint${NC}"
    echo "POST $BASE_URL/goals/$GOAL_ID/notes"
    curl -X POST "$BASE_URL/goals/$GOAL_ID/notes" \
      -H "Content-Type: application/json" \
      -d '{
        "note": "Completata presentazione al cliente",
        "note_source": "frontend"
      }' | jq .

else
    echo -e "${YELLOW}⚠️  No goals found. Create one first with Test 1.${NC}"
fi

echo -e "\n${GREEN}═════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Test Suite Complete${NC}"
echo -e "${GREEN}═════════════════════════════════════════════════════${NC}"

# Additional Info
echo -e "\n${YELLOW}📝 Note: For agent-source notes via Orchestrator:${NC}"
echo "1. Call orchestrator with: 'Aggiungi nota all'obiettivo Aumentare fatturato Q1: Ho contattato altri lead'"
echo "2. Orchestrator invoca project-goal-writer-reader agent"
echo "3. Agent uses search-goal to find goal by title"
echo "4. Agent uses update-goal with note_source='agent'"
echo "5. Note appears in note_history with agent source"
