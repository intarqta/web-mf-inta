import axios from 'axios'

const taskURL = axios.create({
    baseURL: "http://127.0.0.1:8000/api/api/v1/api/"
})

export const taskApi = () => {
 return taskURL.get('/')
}

export const createTask = (task) =>{
    return taskURL.post('/', task)
}
