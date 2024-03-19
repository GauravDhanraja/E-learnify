<?php

$con = new mysqli("localhost", "elearnify-admin", "userAdmin@127", "ElearnifyDB");
if ($con->connect_error) {
    die("Connection failed: " . $con->connect_error);
}

$email = mysqli_real_escape_string($con, $_POST['email']); 
$password = $_POST['password'];

$sql = "SELECT * FROM Students WHERE emailaddress = ?";
$stmt = $con->prepare($sql);
$stmt->bind_param("s", $email); 
$stmt->execute();
$result = $stmt->get_result();
if ($result->num_rows > 0) {
    $row = $result->fetch_assoc();
    if (password_verify($password, $row['password'])) {
        $_SESSION['email'] = $email;
        $_SESSION['user_id'] = $row['id']; 
        header(Location: home.html);
        exit(); 
    } else {
        echo "Invalid password";
    }
} else {
    echo "Invalid email address";
}
$stmt->close();
$con->close();
?>
