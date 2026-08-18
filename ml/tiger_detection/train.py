def training_command(data_yaml:str,epochs:int=50): return ["yolo","detect","train",f"data={data_yaml}",f"epochs={epochs}"]
