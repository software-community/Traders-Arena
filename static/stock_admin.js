//JavaScript for dynamic input field generation -->

// Array to store stock entries (add stock to remove stock row transition, used for closing prices rows auto-generation)
let stockEntries = [];

// The first stock input field row is created using onload
window.onload = function () {
  var initialDiv = document.getElementById("stockInputsContainer");

  var inputDiv = document.createElement("div");
  inputDiv.className = "flex items-center gap-4";

  var inputFields = createInputField();
  inputDiv.appendChild(inputFields[0]);
  inputDiv.appendChild(inputFields[1]);

  var addButton = createButton("Add Stock", function () {
    addInputField(this);
  });

  inputDiv.appendChild(addButton);
  initialDiv.appendChild(inputDiv);
};

// Function to create an input stock field with specified attributes
function createInputField() {
  var stockNameInput = document.createElement("input");
  stockNameInput.type = "text";
  stockNameInput.name = "stockName";
  stockNameInput.className = "w-2/5 px-4 py-2 rounded-lg";
  stockNameInput.placeholder = "Stock Name";

  var priceInputContainer = document.createElement("div");
  priceInputContainer.className = "relative w-1/5";

  var rupeeSymbol = document.createElement("span");
  rupeeSymbol.className = "absolute inset-y-0 left-0 flex items-center pl-4 text-gray-300";
  rupeeSymbol.innerHTML = "&#x20b9;";

  var priceInput = document.createElement("input");
  priceInput.type = "number";
  priceInput.name = "price";
  priceInput.className = "pl-10 py-2 rounded-lg w-full";
  priceInput.placeholder = "Price";

  priceInputContainer.appendChild(rupeeSymbol);
  priceInputContainer.appendChild(priceInput);

  return [stockNameInput, priceInputContainer];
}

// function to create Buttons (Add Stock, Remove specficically)
function createButton(
  label,
  onClick,
  additionalClasses = "neumorph-button px-6 py-2 text-gray-300 font-medium text-sm"
) {
  var button = document.createElement("button");
  button.innerHTML = label;
  button.type = "button";
  button.onclick = onClick;
  button.className = additionalClasses;
  return button;
}

// function to create a new input field once add stock clicked
//      and to also replace clicked "add stock" button with "remove" button
//      disables input fields once added
//      prevents add stock from working if no user input
function addInputField(button) {
  var parentDiv = button.parentNode;
  var stockNameInput = parentDiv.querySelector("input[type='text']");
  var priceInput = parentDiv.querySelector("input[type='number']");

  if (stockNameInput.value && priceInput.value) {
    stockEntries.push({
      name: stockNameInput.value,
      price: priceInput.value,
    });
    
    // Disable the inputs after adding
    stockNameInput.disabled = true;
    priceInput.disabled = true;
  } else {
    alert('Please fill in both stock name and price before adding');
    return;
  }

  var delButton = createButton("Remove", function () {
    removeStock(stockNameInput.value);
    parentDiv.remove();
  }, "neumorph-button px-6 py-2 text-red-400 font-medium text-sm hover:text-red-300");

  parentDiv.appendChild(delButton);

  var newRowDiv = document.createElement("div");
  newRowDiv.className = "flex items-center gap-4";

  var inputFields = createInputField();
  newRowDiv.appendChild(inputFields[0]);
  newRowDiv.appendChild(inputFields[1]);

  var addButton = createButton("Add Stock", function () {
    addInputField(this);
  });
  newRowDiv.appendChild(addButton);

  parentDiv.parentNode.appendChild(newRowDiv);
}

// Closing Prices:
// remove closing price row for corresponding stock selectively
function removeStock(stockName) {
  // Remove the stock name element
  const stockItems = document.querySelectorAll(
    `.stock-item[stock="${stockName}"]`
  );
  stockItems.forEach((item) => item.remove());
  
  // Remove from stockEntries array
  stockEntries = stockEntries.filter(entry => entry.name !== stockName);
}

// Closing Price Fields generation: (takes stock names automaitcally from filled user entries)
function displayStockNames() {
  const roundsValue = document.getElementById("rounds").value;
  if (!roundsValue || roundsValue <= 0) {
    alert('Please enter a valid number of rounds');
    return;
  }
  
  // Collect current stock entries from the form
  const stockNameInputs = document.querySelectorAll('input[name="stockName"]');
  const priceInputs = document.querySelectorAll('input[name="price"]');
  
  // Clear and repopulate stockEntries array
  stockEntries = [];
  stockNameInputs.forEach((input, index) => {
    if (input.value.trim() && priceInputs[index] && priceInputs[index].value.trim()) {
      stockEntries.push({
        name: input.value.trim(),
        price: priceInputs[index].value.trim(),
      });
    }
  });
  
  if (stockEntries.length === 0) {
    alert('Please add at least one stock before entering rounds');
    return;
  }
  
  document.getElementById("closingPrices").style.display = "block";
  var displayContainer = document.getElementById("stockDisplayContainer");
  var x = parseInt(roundsValue);
  displayContainer.innerHTML = ""; // Clear previous entries
  
  for (var j = 1; j <= x; j++) {
    var roundEntry = document.createElement("div");
    roundEntry.className = "mb-4";
    roundEntry.innerHTML =
      '<label class="block text-gray-300 font-light mb-2">Round ' +
      j.toString() +
      "</label>";
    displayContainer.appendChild(roundEntry);
    
    for (var i = 0; i < stockEntries.length; i++) {
      var row = document.createElement("div");
      row.className = "stock-item flex items-center gap-4 mb-2";
      row.setAttribute("stock", stockEntries[i].name);
      var stockEntry = document.createElement("div");
      stockEntry.className = "text-gray-300 w-1/3";
      stockEntry.innerHTML = stockEntries[i].name + " : ";
      row.appendChild(stockEntry);
      var priceInputContainer = document.createElement("div");
      priceInputContainer.className = "relative w-1/5";

      var rupeeSymbol = document.createElement("span");
      rupeeSymbol.className = "absolute inset-y-0 left-0 flex items-center pl-4 text-gray-300";
      rupeeSymbol.innerHTML = "&#x20b9;";

      var priceInput = document.createElement("input");
      priceInput.type = "number";
      priceInput.className = "pl-10 py-2 rounded-lg w-full";
      priceInput.name = "round-" + stockEntries[i].name;
      priceInput.placeholder = "Price";
      priceInput.required = true;

      priceInputContainer.appendChild(rupeeSymbol);
      priceInputContainer.appendChild(priceInput);
      row.appendChild(priceInputContainer);

      roundEntry.appendChild(row);
    }
  }
}
