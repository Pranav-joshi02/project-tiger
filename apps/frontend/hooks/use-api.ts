import {useEffect,useState} from "react";
export function useApi<T>(loader:()=>Promise<T>){const [data,setData]=useState<T>();const [error,setError]=useState<Error>();useEffect(()=>{loader().then(setData).catch(setError)},[]);return {data,error}}
