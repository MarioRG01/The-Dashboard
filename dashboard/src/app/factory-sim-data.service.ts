import { Injectable } from '@angular/core';
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { collection, getDocs } from "firebase/firestore";
import { getFirestore } from "firebase/firestore";
import { doc, getDoc } from "firebase/firestore";

@Injectable({
  providedIn: 'root'
})
export class FactorySimDataService {
  firebaseConfig = {
    apiKey: "AIzaSyDubTcGa7qc1co_05LHjCpapSqXXVHPJKc",
    authDomain: "factorysim-20ceb.firebaseapp.com",
    databaseURL: "https://factorysim-20ceb-default-rtdb.firebaseio.com",
    projectId: "factorysim-20ceb",
    storageBucket: "factorysim-20ceb.appspot.com",
    messagingSenderId: "948040349714",
    appId: "1:948040349714:web:6e37e11b96bd38d51b80cb",
    measurementId: "G-96L6FD5NME"
  }
  app = initializeApp(this.firebaseConfig);
  db = getFirestore(this.app);

  data: Object = {};

  dataFetched: boolean = false;

  constructor() { }

  async fetchAllData(){
    const querySnapshot = await getDocs(collection(this.db, "123"));
    querySnapshot.forEach((doc) => {
      console.log(doc.data());
    });
  }

  async fetchDataById(seed:string, id: string){
    const docRef = doc(this.db, seed, id);
    const docSnap = await getDoc(docRef);

    if (docSnap.exists()) {
      console.log("Document data:", docSnap.data());
      this.dataFetched = true;
      this.data = docSnap.data()
    } else {
      // docSnap.data() will be undefined in this case
      console.log("No such document!");
    }
  }

  getTotalProduction(){
    if('production' in this.data) {
      const totalProduction = (this.data.production as {total: {}}).total
      console.log("getting data production")
      return totalProduction
    }else{
      console.log("no data information")
      return null
    }
  }

  getDailyProduction(){
    if('production' in this.data) {
      const totalProduction = (this.data.production as {daily: {}}).daily
      console.log("getting data production")
      return totalProduction
    }else{
      console.log("no data information")
      return null
    }
  }
}
