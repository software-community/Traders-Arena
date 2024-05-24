//JavaScript for dynamic input field generation -->

// Array to store stock entries (add stock to remove stock row transition, used for closing prices rows auto-generation)
let stockEntries = [];

// The first stock input field row is created using onload
window.onload = function () {
  var initialDiv = document.getElementById("stockInputsContainer");

  var inputDiv = document.createElement("div");
  inputDiv.className = "flex items-center mb-2";

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
  stockNameInput.className = "w-2/5 px-3 py-2 border rounded-md mr-2 bg-gray-900";
  stockNameInput.placeholder = "Stock Name";

  var priceInputContainer = document.createElement("div");
  priceInputContainer.className = "relative w-1/5 mr-2";

  var rupeeSymbol = document.createElement("span");
  rupeeSymbol.className = "absolute inset-y-0 left-0 flex items-center pl-2 text-lg";
  rupeeSymbol.innerHTML = "&#x20b9;";

  var priceInput = document.createElement("input");
  priceInput.type = "number";
  priceInput.className = "pl-8 py-2 border rounded-md w-full bg-gray-900";
  priceInput.placeholder = "Price";

  priceInputContainer.appendChild(rupeeSymbol);
  priceInputContainer.appendChild(priceInput);

  return [stockNameInput, priceInputContainer];
}

// function to create Buttons (Add Stock, Remove specficically)
function createButton(label, onClick, additionalClasses = "bg-blue-500 text-white px-4 py-2 rounded-md w-1/6 ml-auto") {
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
  var stockNameInput = parentDiv.querySelector('input[type="text"]');
  var priceInput = parentDiv.querySelector('input[type="number"]');

  // Get the values from the input fields
  var stockName = stockNameInput.value;
  var price = priceInput.value;
  stockNameInput.name = "stockName";
  stockNameInput.readOnly = true;
  stockNameInput.style.border = "none";
  priceInput.name = "price";
  priceInput.readOnly = true;
  priceInput.style.border = "none";

  // Add the values to the stockEntries array
  if (stockName && price) {
    stockEntries.push({ name: stockName, price: price });
    console.log(stockEntries);
  } else {
    alert("Please enter both stock name and price.");
    return;
  }

  //Remove button has two functions 
  //  - to only remove one stock field
  //  - or if closing price entries have been given, then to also remove closing price row for corresponding stock selectively 
  var delButton = createButton("Remove", function () {
    var index = stockEntries.findIndex(entry => entry.name === stockName && entry.price == price);
    if (index !== -1) {
      stockEntries.splice(index, 1);
      console.log(stockEntries);
      // displayStockNames(stockEntries.length);
    }
    if (document.getElementById("closingPrices").style.display == "block") {
      removeStock(stockName);
      //remove closing price row for corresponding stock selectively if its being used
    }
    parentDiv.remove();

  }, "bg-red-500 hover:bg-red-700 text-white px-4 py-2 rounded-md w-1/6 ml-auto");

  parentDiv.removeChild(button);
  parentDiv.appendChild(delButton);

  var newRowDiv = document.createElement("div");
  newRowDiv.className = "flex items-center mb-2";

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
  const stockItems = document.querySelectorAll(`.stock-item[stock="${stockName}"]`);
  stockItems.forEach(item => item.remove());
}


// Closing Price Fields generation: (takes stock names automaitcally from filled user entries)
function displayStockNames() {
  document.getElementById("closingPrices").style.display = "block";
  var displayContainer = document.getElementById("stockDisplayContainer");
  var x = document.getElementById("rounds").value;
  displayContainer.innerHTML = ""; // Clear previous entries
  for (var j = 1; j <= x; j++) {
    var roundEntry = document.createElement("div");
    roundEntry.className = "mb-2";
    roundEntry.innerHTML = '<label for="rounds" class="block text-white-700 font mb-2 ml-2">Round ' + j.toString() + ' - </label';
    displayContainer.appendChild(roundEntry);
    for (var i = 0; i < stockEntries.length; i++) {
      var row = document.createElement("div");
      row.className = "stock-item flex items-center mb-2";
      row.setAttribute("stock", stockEntries[i].name);
      var stockEntry = document.createElement("div");
      stockEntry.className = "mb-2 ml-4 mr-2 w-1/3";
      stockEntry.innerHTML = stockEntries[i].name + ' : ';
      row.appendChild(stockEntry);
      var priceInputContainer = document.createElement("div");
      priceInputContainer.className = "relative w-1/5 mr-2";

      var rupeeSymbol = document.createElement("span");
      rupeeSymbol.className = "absolute inset-y-0 left-0 flex items-center pl-2 text-lg";
      rupeeSymbol.innerHTML = "&#x20b9;";

      var priceInput = document.createElement("input");
      priceInput.type = "number";
      priceInput.className = "pl-8 py-2 border rounded-md w-full bg-gray-900";
      priceInput.name = "round-" + stockEntries[i].name;
      priceInput.placeholder = "Price";

      priceInputContainer.appendChild(rupeeSymbol);
      priceInputContainer.appendChild(priceInput);
      row.appendChild(priceInputContainer);

      roundEntry.appendChild(row);
    }
  }
}


