const oneWayBtn = document.getElementById("oneway-btn");
const roundTripBtn = document.getElementById("roundtrip-btn");
const returnDate = document.getElementById("return");

returnDate.disabled = true; 
returnDate.classList.add("hidden");

// --- One Way button click ---
oneWayBtn.addEventListener("click", () => {
  oneWayBtn.classList.add("active");
  roundTripBtn.classList.remove("active");

  returnDate.disabled = true;
  returnDate.classList.add("hidden");
});

// --- Round Trip button click ---
roundTripBtn.addEventListener("click", () => {
  roundTripBtn.classList.add("active");
  oneWayBtn.classList.remove("active");

  returnDate.disabled = false;
  returnDate.classList.remove("hidden");
});



