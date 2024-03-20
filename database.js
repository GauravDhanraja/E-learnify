
 const firebaseConfig = {
  apiKey: "AIzaSyCJDBD-RHhkpP6sStStCnimkBpyIRJ3bm4",
  authDomain: "e-learnify-898a1.firebaseapp.com",
  databaseURL: "https://e-learnify-898a1-default-rtdb.firebaseio.com",
  projectId: "e-learnify-898a1",
  storageBucket: "e-learnify-898a1.appspot.com",
  messagingSenderId: "895920268281",
  appId: "1:895920268281:web:40bf3baa90d2d314975328",
  measurementId: "G-N5PZQLHT2Z"
};

  //initialize firebase
  firebase.initializeApp(firebaseConfig);
  
  //reference your database
 
 var loginDB = firebase.database().ref('login');
 document.getElementById()