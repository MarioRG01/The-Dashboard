import { Component, Input, OnInit, OnChanges } from '@angular/core';
import { FactorySimDataService } from '../factory-sim-data.service';
import { NgxChartsModule } from '@swimlane/ngx-charts';

@Component({
  selector: 'app-pie-chart-graphic',
  templateUrl: './pie-chart-graphic.component.html',
  styleUrls: ['./pie-chart-graphic.component.scss'],
  standalone: true,
  imports: [ NgxChartsModule]
})
export class PieChartGraphicComponent implements OnChanges{
  @Input() activeTimePeriod: string = ''
  @Input() timePeriod1: string = ''
  @Input() timePeriod2: string = ''
  @Input() mode: string = ''

  single: any[] = [];
  view: Number[] = [700, 400];

  // options
  gradient: boolean = true;
  showLegend: boolean = true;
  showLabels: boolean = true;
  isDoughnut: boolean = false;
  legendPosition: string = 'below';

  colorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };

  constructor(public factorySimDataService: FactorySimDataService){
    if(!this.factorySimDataService.dataFetched){
      this.fetchAllData();
    }else{
      //this.getTotalProdcution();
    }
    const single = [
      {
        "name": "Germany",
        "value": 8940000
      },
      {
        "name": "USA",
        "value": 5000000
      },
      {
        "name": "France",
        "value": 7200000
      },
        {
        "name": "UK",
        "value": 6200000
      }
    ];
    Object.assign(this, { single });
  }

  drawGraph(){
    let single: any = null
    if(this.mode === 'status'){
      single = this.getGraphValues();
    }else{
      single = this.getGraphValues2();
    }
    Object.assign(this, { single });
  }

  getGraphValues(){
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
    let inOrder = 0
    let incomplete = 0
    let done = 0
    let failed = 0
    let aborted = 0
    console.log("dailyProd", dailyProd)
    console.log("ordered", orderedDays),
    console.log("dates", this.timePeriod1, this.timePeriod2)
    const daysInPeriod = []
    for(let day in orderedDays){
      day = orderedDays[day]
      if(this.compareDates(day, this.timePeriod2) == 1) {
        console.log(1, day)
        break
      }
      if(this.compareDates(day, this.timePeriod1) == 0 || this.compareDates(day, this.timePeriod1) == 1) {
        console.log(-1, day)
        done += dailyProd[day].factory.productsFinished
        failed += dailyProd[day].factory.productsFailed
        aborted += dailyProd[day].factory.productsAborted
        daysInPeriod.push(day)
      }
      if(this.compareDates(day, this.timePeriod2) == 0){
        console.log(0, day)
        inOrder = dailyProd[day].factory.productsOrdered
        incomplete = dailyProd[day].factory.productsIncomplete
        break
      }
    }
    console.log("daysPeriod", daysInPeriod)
    dayValues.push({"name": "InOrder","value": inOrder})
    dayValues.push({"name": "Incomplete","value": incomplete})
    dayValues.push({"name": "Done","value": done})
    dayValues.push({"name": "Failed","value": failed})
    dayValues.push({"name": "Aborted","value": aborted})

    /*console.log(totalFactoryProd["productsPlanned"])
    values.push({"In Order": totalFactoryProd["productsPlanned"]})
    values.push({"Incomplete": totalFactoryProd["productsIncomplete"]})
    values.push({"Done": totalFactoryProd["productsFinished"]})
    values.push({"Failed": totalFactoryProd["productsFailed"]})
    values.push({"Aborted": totalFactoryProd["productsAborted"]})*/
    return dayValues
  }

  getGraphValues2(){
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
    let shutdowns = 0
    console.log("dailyProd", dailyProd)
    console.log("ordered", orderedDays),
    console.log("dates", this.timePeriod1, this.timePeriod2)
    const daysInPeriod = []
    for(let day in orderedDays){
      day = orderedDays[day]
      if(this.compareDates(day, this.timePeriod2) == 1) {
        console.log(1, day)
        break
      }
      if(this.compareDates(day, this.timePeriod1) == 0 || this.compareDates(day, this.timePeriod1) == 1) {
        console.log(-1, day)
        shutdowns += (dailyProd[day].factory.shutdown ? 1 : 0)
        daysInPeriod.push(day)
      }
      if(this.compareDates(day, this.timePeriod2) == 0){
        console.log(0, day)
        break
      }
    }
    console.log("daysPeriod", daysInPeriod)
    dayValues.push({"name": "Active Days","value": daysInPeriod.length - shutdowns})
    dayValues.push({"name": "Shutdowns","value": shutdowns})

    /*console.log(totalFactoryProd["productsPlanned"])
    values.push({"In Order": totalFactoryProd["productsPlanned"]})
    values.push({"Incomplete": totalFactoryProd["productsIncomplete"]})
    values.push({"Done": totalFactoryProd["productsFinished"]})
    values.push({"Failed": totalFactoryProd["productsFailed"]})
    values.push({"Aborted": totalFactoryProd["productsAborted"]})*/
    return dayValues
  }

  parseDate(dateString: string) {
    const parts = dateString.split('/');
    const day = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1; // Months are zero-indexed (January is 0)
    const year = parseInt(parts[2], 10);
    return new Date(year, month, day);
  }

  async fetchAllData() {
    try {
      const result = await this.factorySimDataService.fetchDataById("sim", "1"); // Wait for the data to be fetched
      //this.getTotalProdcution();
      this.drawGraph()
    } catch (error) {
        console.error('Error fetching data:', error);
    }
  }

  getTotalProdcution(){
    return this.factorySimDataService.getTotalProduction()
  }

  getDailyProduction() {
    return this.factorySimDataService.getDailyProduction()
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

}
