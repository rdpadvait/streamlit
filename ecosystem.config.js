module.exports = {
  apps : [{
    name   : "streamlit-dub",
    script : "/home/ubuntu/pm2/streamlit/pm2.sh", 
    args   : "",
    cwd    : "/home/ubuntu/pm2/streamlit", 
    interpreter: "bash",   
    autorestart: true,    
    watch  : false,        
    log_date_format: "YYYY-MM-DD HH:mm Z"
  }]
};