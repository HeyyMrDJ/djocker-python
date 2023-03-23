package main

import (
    "io"
    "fmt"
    "net/http"
)

func main() {
    http.HandleFunc("/", HelloServer)
    http.ListenAndServe(":8080", nil)
}

func HelloServer(w http.ResponseWriter, r *http.Request) {
    io.WriteString(w, "Hello from server")
    fmt.Println("Page hit")
}
