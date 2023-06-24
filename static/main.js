
document.addEventListener('DOMContentLoaded', () => {
    let general = document.getElementById('general')
    let all_checkboxes = document.getElementsByName('tracks')
    let all_playlist_items = document.getElementsByName('playlist-item')
    
    function selectAll (div_targets) {
    if (general){
      general.addEventListener('click', () => {
        general.checked === true ?
        div_targets.forEach(div_target => {
            div_target.checked = true
        }) 
        :
        div_targets.forEach(div_target => {
            div_target.checked = false
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
    let sources = document.querySelectorAll('.onclick-source')
    let target = document.querySelectorAll('.onclick-target')
    let sourceMain = document.querySelector(".source-main")
    let targetMain = document.querySelector(".target-main")
    let sourceId = ''
    let targetId = ''
    let sourceName = ''
    let targetName = ''
    let sourceImage = ''
    let targetImage = ''
    let sourceSnapshot= ''
    let targetSnapshot = ''

    if (targetMain) {
      targetMain.style.display = 'None'

    }

    function selectSource(){
      sources.forEach(source => {
        source.addEventListener('click', () => {
          sourceMain.style.display = 'None'
          targetMain.style.display = 'flex'
          sourceId = source.dataset.id
          sourceName = source.dataset.name
          sourceImage = source.dataset.image
          sourceSnapshot = source.dataset.snapshotid
        })
      })
    }

     function selectTarget(){
      target.forEach(target => {
        target.addEventListener('click', () => {
          targetMain.style.display = 'None'
          targetId = target.dataset.id
          targetName = target.dataset.name
          targetImage = target.dataset.image
          targetSnapshot = target.dataset.snapshotid

          let sourceTarget = {
            'sourceId': sourceId, 
            'sourceName': sourceName,
            'sourceImage': sourceImage,
            'sourceSnapshot':sourceSnapshot,
            'targetId': targetId, 
            'targetName': targetName,
            'targetImage': targetImage,
            'targetSnapshot':targetSnapshot,
          }

          const formData = new FormData();
          formData.append('playlistids', JSON.stringify(sourceTarget))
          fetch('/playlists', {
              method: 'POST',
              body: formData
          })
          .then(response => {
              if (response.ok) {
                  console.log(response)
                return response.json();
              } else {
                throw new Error('data send failed');
              }
            })
            .then(data => {
              console.log('Server response:', data);
              window.location.href = "/playlists/transfer";
            })
            .catch(error => {
              console.error('Error sending data', error);
              window.location.href = "/playlists";
              alert('An error occured. Please try again')
            });
        })
      })
    }

    selectSource()
    selectTarget()
    selectAll(all_checkboxes)
    selectAll(all_playlist_items)

})

