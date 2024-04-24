import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { FactorySimDataService } from '../factory-sim-data.service';

@Component({
  selector: 'app-bar-chart-graphic',
  templateUrl: './bar-chart-graphic.component.html',
  styleUrls: ['./bar-chart-graphic.component.scss'],
  standalone: true,
  imports: [ NgxChartsModule]
})
export class BarChartGraphicComponent implements OnChanges{
  @Input() activeTimePeriod: string = ''
  @Input() timePeriod1: string = ''
  @Input() timePeriod2: string = ''
  @Input() mode: string = ''

  multi: any[] = [];
  view: any[] = [700, 400];

  // options
  showXAxis: boolean = true;
  showYAxis: boolean = true;
  gradient: boolean = false;
  showLegend: boolean = true;
  showXAxisLabel: boolean = true;
  xAxisLabel: string = 'Workstations id';
  showYAxisLabel: boolean = true;
  yAxisLabel: string = 'Time';
  animations: boolean = true;

  colorScheme = {
    domain: ['#5AA454', '#C7B42C', '#AAAAAA']
  };

  constructor(public factorySimDataService: FactorySimDataService) {
    if(!this.factorySimDataService.dataFetched){
      this.fetchAllData();
    }else{
      this.drawGraph()
    }
  }

  drawGraph(){
    console.log("draw graph")
    let multi: any = null
    if(this.mode === 'status'){
      multi = this.getGraphValues();
      console.log("DATA", multi)
    }else{
      multi = this.getGraphValues2();
    }
    if(multi){
      Object.assign(this, { multi });
    }
  }

  getGraphValues(){
    if(this.getDailyProduction()){

      const values = []
      const dayValues = []
      //const totalProd: any = this.getTotalProdcution()
      //const totalFactoryProd = totalProd.factory
      const dailyProd: any = this.getDailyProduction()
      const days = []
      for(const day in dailyProd){
        days.push(day)
      }
      const orderedDays = this.sortByDate(days.slice())
      let down = 0
      let idle = 0
      let producing = 0
      let restock = 0
      let start = 0
      console.log("dailyProd", dailyProd)
      console.log("ordered", orderedDays),
      console.log("dates", this.timePeriod1, this.timePeriod2)
      const daysInPeriod = []
      const wks = []
      for(const wk in dailyProd[orderedDays[0]].workstations){
        wks.push({"name": wk.toString(), "series": [{"name": "DOWN", "value": 0}, {"name": "IDLE", "value": 0}, {"name": "PRODUCING", "value": 0}, {"name": "RESTOCK", "value": 0}, {"name": "START", "value": 0}]})
      }
      for(let day in orderedDays){
        day = orderedDays[day]
        if(this.compareDates(day, this.timePeriod2) == 1) {
          console.log(1, day)
          break
        }
        console.log("length", Object.keys(dailyProd[day].workstations).length)
        for(let wk = 0;wk < Object.keys(dailyProd[day].workstations).length; wk++){
          console.log("wk", wk)
          //const wk = parseInt(wk1)
          if(this.compareDates(day, this.timePeriod1) == 0 || this.compareDates(day, this.timePeriod1) == 1) {
            console.log(-1, day)
            wks[wk].series[0].value += dailyProd[day].workstations[wk.toString()].statusTime.DOWN
            wks[wk].series[1].value += dailyProd[day].workstations[wk.toString()].statusTime.IDLE
            wks[wk].series[2].value += dailyProd[day].workstations[wk.toString()].statusTime.PRODUCING
            wks[wk].series[3].value += dailyProd[day].workstations[wk.toString()].statusTime.RESTOCK
            wks[wk].series[4].value += dailyProd[day].workstations[wk.toString()].statusTime.START
            daysInPeriod.push(day)
          }

        }
        if(this.compareDates(day, this.timePeriod2) == 0){
          console.log(0, day)
          break
        }
      }
      console.log("daysPeriod", daysInPeriod)
      return wks
    }
    return null
  }

  getGraphValues2(){

  }


  getDailyProduction() {
    return this.factorySimDataService.getDailyProduction()
  }

  async fetchAllData() {
    try {
      const result = await this.factorySimDataService.fetchDataById("sim", "1"); // Wait for the data to be fetched
      //this.getTotalProdcution();
    } catch (error) {
        console.error('Error fetching data:', error);
    }finally{
      this.drawGraph()
    }
  }

  sortByDate(dates: string[]): string[] {
    return dates.sort((date1, date2) => {
      // Split the date strings into components
      const parts1 = date1.split('/');
      const parts2 = date2.split('/');

      // Convert components to numbers for comparison
      const day1 = parseInt(parts1[0], 10);
      const month1 = parseInt(parts1[1], 10) - 1; // Months are zero-indexed in JavaScript
      const year1 = parseInt(parts2[2], 10);

      const day2 = parseInt(parts2[0], 10);
      const month2 = parseInt(parts2[1], 10) - 1;
      const year2 = parseInt(parts2[2], 10);

      // Compare dates chronologically (year, month, day)
      if (year1 < year2) return -1; // date1 is earlier
      if (year1 > year2) return 1; // date2 is earlier

      if (month1 < month2) return -1;
      if (month1 > month2) return 1;

      if (day1 < day2) return -1;
      if (day1 > day2) return 1;

      return 0; // Dates are equal
    });
  }

  compareDates(date1: string, date2: string): number {
    // Split the date strings into components
    const parts1 = date1.split('/');
    const parts2 = date2.split('/');

    // Convert components to numbers for comparison
    const day1 = parseInt(parts1[0], 10);
    const month1 = parseInt(parts1[1], 10) - 1; // Months are zero-indexed in JavaScript
    const year1 = parseInt(parts1[2], 10);

    const day2 = parseInt(parts2[0], 10);
    const month2 = parseInt(parts2[1], 10) - 1;
    const year2 = parseInt(parts2[2], 10);

    // Compare dates chronologically (year, month, day)
    if (year1 < year2) return -1; // date1 is earlier
    if (year1 > year2) return 1; // date2 is earlier

    if (month1 < month2) return -1;
    if (month1 > month2) return 1;

    if (day1 < day2) return -1;
    if (day1 > day2) return 1;

    return 0; // Dates are equal
  }

  ngOnChanges(changes: import('@angular/core').SimpleChanges) {
    if (changes['timePeriod1']) {
    }
    if (changes['timePeriod2']) {
    }
    if (changes['activeTimePeriod']) {
    }
    this.drawGraph()
  }

}
