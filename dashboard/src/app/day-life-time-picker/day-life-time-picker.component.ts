import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonContent, IonHeader, IonTitle, IonToolbar, IonList, IonItem, IonSelect, IonSelectOption } from '@ionic/angular/standalone';
import { IonToggle } from "@ionic/angular/standalone";

@Component({
  selector: 'app-day-life-time-picker',
  templateUrl: './day-life-time-picker.component.html',
  styleUrls: ['./day-life-time-picker.component.scss'],
  standalone: true,
  imports: [IonList, IonContent, IonHeader, IonTitle, IonToolbar, IonToggle, CommonModule, FormsModule, IonItem, IonSelect, IonSelectOption]
})
export class DayLifeTimePickerComponent  implements OnInit {
  timePeriod: string = 'all'
  @Output() sendTP = new EventEmitter<any>(); // Define the event emitter

  constructor() { }

  ngOnInit() {
    1 == 1
  }

  onTimePeriodChange(event: any){
    this.timePeriod = event.detail.value
    this.sendTimePeriod()
    console.log(this.timePeriod)
  }

  sendTimePeriod() {
    this.sendTP.emit(this.timePeriod); // Emit data or event when triggered
  }


}
