This is a sandbox for exploring embodied LLM agents in a cash register game setting.

# Brainstorming

## Checkout
if the player initiates a checkout (or should they always be in the checkout state?)
and a customer is present
sum up the cost total of the items
player inputs that into the register
  - if its wrong, customer patience decreases by fixed amount
customer leaves when checked out or patiences is empty
  - if patience runs out, player gets no money
  - successful checkouts, player nets the money (eventually add some sort of cost for the goods)
