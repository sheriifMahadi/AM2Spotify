
document.addEventListener('DOMContentLoaded', () => {
    let general = document.getElementById('general')
    let all_checkboxes = document.getElementsByName('tracks')
    function selectAll () {
    if (general){
      general.addEventListener('click', () => {
        general.checked === true ?
        all_checkboxes.forEach(checkbox => {
            checkbox.checked = true
        }) 
        :
        all_checkboxes.forEach(checkbox => {
            checkbox.checked = false
        })          
    })
    }
       
    }
    let uploadBtn = document.getElementById('upload')
    let fileForm = document.getElementById('customInput')
    if (uploadBtn) {
        uploadBtn.addEventListener('click', (event) => {
            const formData = new FormData();
            event.preventDefault()
            const file = fileForm.files[0]
            formData.append('file', file)
            
            fetch('/upload', {
                method: 'POST',
                body: formData,
            })
            .then(response => {
                if (response.ok) {
                    console.log(response)
                  return response.json();
                } else {
                  throw new Error('File upload failed');
                }
              })
              .then(data => {
                console.log('Server response:', data);
                window.location.href = "/import";
              })
              .catch(error => {
                console.error('Error uploading file:', error);
              });
            
        })
    }
    


    selectAll()
    
    
})
